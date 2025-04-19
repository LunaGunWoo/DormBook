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
    serializer_class = BookInductionTimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=BookInductionTimeSlotSerializer,
        responses={
            200: openapi.Response("예약 성공", ListInductionTimeSlotSerializer),
            201: openapi.Response(
                "예약 및 슬롯 생성 성공", ListInductionTimeSlotSerializer
            ),  # 새로 생성된 경우 201
            400: "잘못된 요청 (입력 값 오류, 사용 불가 인덕션, 이미 예약됨 등)",
            404: "인덕션을 찾을 수 없음",
            409: "동시 예약 시도 충돌 (Conflict)",  # 동시성 문제 발생 시
            500: "서버 내부 오류",
        },
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
        end_time = start_time + timedelta(minutes=30)

        try:
            with transaction.atomic():
                (
                    time_slot,
                    created,
                ) = InductionTimeSlot.objects.select_for_update().get_or_create(
                    induction=induction,
                    start_time=start_time,
                    defaults={"end_time": end_time},
                )

                if not created and time_slot.user is not None:
                    return Response(
                        {"error": "이미 예약된 시간입니다"},
                        status=status.HTTP_409_CONFLICT,
                    )
                time_slot.book(request.user)
            response_serializer = ListInductionTimeSlotSerializer(time_slot)
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response(response_serializer.data, status=status_code)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error during booking: {e}")
            return Response(
                {"error": "예약 처리 중  서버 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
