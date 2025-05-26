from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import *
from .models import *
from datetime import datetime, timedelta


class InductionListAPIView(generics.ListAPIView):
    queryset = Induction.objects.all()
    serializer_class = InductionSerializer
    permission_classes = [permissions.IsAuthenticated]


class InductionTimeSlotListAPIView(generics.ListAPIView):
    serializer_class = ListInductionTimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "date",
                openapi.IN_QUERY,
                description="조회할 날짜 (YYYY-MM-DD 형식)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                required=True,
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            if not self.request.query_params.get("date"):
                return InductionTimeSlot.objects.none()

        induction_pk = self.kwargs.get("pk")
        date_str = self.request.query_params.get("date")

        if not date_str:
            raise serializers.ValidationError("날짜를 지정해주세요.")

        try:
            query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise serializers.ValidationError("날짜 형식이 잘못되었습니다.")

        start_dt = timezone.make_aware(
            datetime.combine(query_date, datetime.min.time()),
            timezone.get_default_timezone(),
        )
        end_dt = start_dt + timedelta(days=1)

        queryset = InductionTimeSlot.objects.filter(
            induction__pk=induction_pk,
            start_time__gte=start_dt,
            start_time__lt=end_dt,
            user__isnull=False,
        ).select_related("user", "induction")

        return queryset


class InductionTimeSlotBookAPIView(generics.GenericAPIView):
    queryset = InductionTimeSlot.objects.none()
    serializer_class = BookInductionTimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        return {"request": self.request, "format": self.format_kwarg, "view": self}

    @swagger_auto_schema(
        request_body=BookInductionTimeSlotSerializer,
        responses={
            200: openapi.Response(
                "기존 슬롯 예약 성공", ListInductionTimeSlotSerializer(many=True)
            ),
            201: openapi.Response(
                "새 슬롯 생성 및 예약 성공", ListInductionTimeSlotSerializer(many=True)
            ),
            400: "잘못된 요청 (입력 값 오류, 사용 불가 인덕션, 예약 한도 초과 등)",
            404: "인덕션을 찾을 수 없음",
            409: "동시 예약 시도 충돌 또는 이미 예약된 슬롯",
            500: "서버 내부 오류",
        },
        operation_description="인덕션 특정 시간 슬롯 예약. 30분 또는 60분 단위로 예약 가능. 하루 최대 3번의 예약 가능",
    )
    def post(self, request, pk):
        induction = get_object_or_404(Induction, pk=pk)
        if not induction.is_available:
            return Response(
                {"error": "사용 불가능한 인덕션입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        start_time = serializer.validated_data["start_time"]
        duration_minutes = serializer.validated_data.get(
            "duration_minutes", SLOT_DURATION_MINUTES
        )
        num_slots_to_book = duration_minutes // SLOT_DURATION_MINUTES

        booked_slot_objects = []
        any_slot_newly_created_in_db = False

        timestamp_for_this_booking_action = timezone.now()

        try:
            with transaction.atomic():
                for i in range(num_slots_to_book):
                    current_slot_start_time = start_time + timedelta(
                        minutes=i * SLOT_DURATION_MINUTES
                    )
                    current_slot_end_time = current_slot_start_time + timedelta(
                        minutes=SLOT_DURATION_MINUTES
                    )

                    (
                        slot,
                        created,
                    ) = InductionTimeSlot.objects.select_for_update().get_or_create(
                        induction=induction,
                        start_time=current_slot_start_time,
                        defaults={
                            "end_time": current_slot_end_time,
                            "user": request.user,
                            "booked_at": timestamp_for_this_booking_action,
                        },
                    )

                    if created:
                        any_slot_newly_created_in_db = True
                        booked_slot_objects.append(slot)
                    else:
                        if slot.user is None:
                            slot.user = request.user
                            slot.booked_at = timestamp_for_this_booking_action
                            slot.end_time = current_slot_end_time
                            slot.save()
                            booked_slot_objects.append(slot)
                        elif slot.user == request.user:
                            raise ValueError(
                                f"{current_slot_start_time.strftime('%H:%M')} 슬롯은 이미 본인의 이전 예약에 포함되어 있습니다. "
                                "기존 예약을 취소 후 다시 시도해주세요."
                            )
                        else:
                            raise ValueError(
                                f"{current_slot_start_time.strftime('%H:%M')} 슬롯은 이미 다른 사용자가 예약했습니다."
                            )

            response_serializer = ListInductionTimeSlotSerializer(
                booked_slot_objects, many=True
            )
            status_code = (
                status.HTTP_201_CREATED
                if any_slot_newly_created_in_db
                else status.HTTP_200_OK
            )

            return Response(response_serializer.data, status=status_code)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)
        except Exception as e:
            print(f"Error during booking: {e}")
            return Response(
                {"error": "예약 처리 중 예측하지 못한 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
