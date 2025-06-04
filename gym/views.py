from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction, IntegrityError
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from datetime import datetime, timedelta

from .models import Treadmill, TreadmillTimeSlot, Cycle, CycleTimeSlot
from .serializers import (
    TreadmillSerializer,
    ListTreadmillTimeSlotSerializer,
    BookTreadmillTimeSlotSerializer,
    CycleSerializer,
    ListCycleTimeSlotSerializer,
    BookCycleTimeSlotSerializer,
    SLOT_DURATION_MINUTES_GYM,
)


class BaseMachineListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]


class BaseTimeSlotListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "date",
                openapi.IN_QUERY,
                description="조회할 날짜 (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                required=True,
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(
            self, "swagger_fake_view", False
        ) and not self.request.query_params.get("date"):
            return self.model_class.objects.none()

        machine_pk = self.kwargs.get("pk")

        get_object_or_404(self.machine_model_class, pk=machine_pk)

        date_str = self.request.query_params.get("date")
        if not date_str:
            raise ValidationError("날짜를 'date' 파라미터로 지정해주세요 (YYYY-MM-DD).")
        try:
            query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("날짜 형식이 잘못되었습니다. (YYYY-MM-DD)")

        start_dt = timezone.make_aware(
            datetime.combine(query_date, datetime.min.time())
        )
        end_dt = start_dt + timedelta(days=1)

        filter_kwargs = {
            f"{self.machine_fk_field}__pk": machine_pk,
            "start_time__gte": start_dt,
            "start_time__lt": end_dt,
            "user__isnull": False,
        }
        return self.model_class.objects.filter(**filter_kwargs).select_related(
            "user", self.machine_fk_field
        )


class BaseTimeSlotBookAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs.setdefault("context", self.get_serializer_context())

        if hasattr(serializer_class, "timeslot_model"):

            serializer_class.timeslot_model = self.model_class

        return serializer_class(*args, **kwargs)

    @swagger_auto_schema(
        responses={
            200: "기존 슬롯 예약 업데이트 성공",
            201: "새 슬롯 생성 및 예약 성공",
            400: "잘못된 요청 (입력 값 오류, 사용 불가 기구, 예약 한도 초과 등)",
            404: "기구를 찾을 수 없음",
            409: "동시 예약 시도 충돌 또는 이미 예약된 슬롯",
            500: "서버 내부 오류",
        },
        operation_id="book_gym_equipment_slot",
        operation_description=f"헬스 기구 특정 시간 슬롯 예약. {SLOT_DURATION_MINUTES_GYM}분 또는 {SLOT_DURATION_MINUTES_GYM*2}분 단위. 하루 최대 2번 예약 행동 가능.",
    )
    def post(self, request, pk):
        machine_instance = get_object_or_404(self.machine_model_class, pk=pk)

        machine_display_name = str(machine_instance)

        if not machine_instance.is_available:
            return Response(
                {"error": f"{machine_display_name}은(는) 현재 사용 불가능합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        start_time = serializer.validated_data["start_time"]
        duration_minutes = serializer.validated_data.get(
            "duration_minutes", SLOT_DURATION_MINUTES_GYM
        )
        num_slots_to_book = duration_minutes // SLOT_DURATION_MINUTES_GYM

        booked_slot_objects = []
        any_slot_newly_created_in_db = False
        timestamp_for_this_booking_action = timezone.now()

        try:
            with transaction.atomic():
                for i in range(num_slots_to_book):
                    current_slot_start_time = start_time + timedelta(
                        minutes=i * SLOT_DURATION_MINUTES_GYM
                    )
                    current_slot_end_time = current_slot_start_time + timedelta(
                        minutes=SLOT_DURATION_MINUTES_GYM
                    )

                    slot_defaults = {
                        "end_time": current_slot_end_time,
                        "user": request.user,
                        "booked_at": timestamp_for_this_booking_action,
                    }
                    slot_filters = {
                        self.machine_fk_field: machine_instance,
                        "start_time": current_slot_start_time,
                    }

                    (
                        slot,
                        created,
                    ) = self.model_class.objects.select_for_update().get_or_create(
                        **slot_filters, defaults=slot_defaults
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
                                f"{current_slot_start_time.strftime('%H:%M')} 슬롯은 이미 본인의 다른 예약에 포함되어 있습니다."
                            )
                        else:
                            raise ValueError(
                                f"{current_slot_start_time.strftime('%H:%M')} 슬롯은 이미 다른 사용자가 예약했습니다."
                            )

            response_serializer_class = self.list_serializer_class
            response_data = response_serializer_class(
                booked_slot_objects, many=True, context=self.get_serializer_context()
            ).data
            status_code = (
                status.HTTP_201_CREATED
                if any_slot_newly_created_in_db
                else status.HTTP_200_OK
            )
            return Response(response_data, status=status_code)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)
        except IntegrityError:
            return Response(
                {
                    "error": "데이터 저장 중 충돌이 발생했습니다. 잠시 후 다시 시도해주세요."
                },
                status=status.HTTP_409_CONFLICT,
            )
        except Exception as e:

            print(f"Error during {self.machine_model_class.__name__} booking: {e}")
            return Response(
                {"error": "예약 처리 중 예측하지 못한 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TreadmillListAPIView(BaseMachineListAPIView):
    queryset = Treadmill.objects.filter(is_available=True)
    serializer_class = TreadmillSerializer


class TreadmillTimeSlotListAPIView(BaseTimeSlotListAPIView):
    serializer_class = ListTreadmillTimeSlotSerializer
    model_class = TreadmillTimeSlot
    machine_model_class = Treadmill
    machine_fk_field = "treadmill"


@swagger_auto_schema(
    request_body=BookTreadmillTimeSlotSerializer,
    responses={
        200: ListTreadmillTimeSlotSerializer(many=True),
        201: ListTreadmillTimeSlotSerializer(many=True),
    },
    operation_id="book_treadmill_slot",
)
class TreadmillTimeSlotBookAPIView(BaseTimeSlotBookAPIView):
    queryset = TreadmillTimeSlot.objects.none()
    serializer_class = BookTreadmillTimeSlotSerializer
    list_serializer_class = ListTreadmillTimeSlotSerializer
    model_class = TreadmillTimeSlot
    machine_model_class = Treadmill
    machine_fk_field = "treadmill"


class CycleListAPIView(BaseMachineListAPIView):
    queryset = Cycle.objects.filter(is_available=True)
    serializer_class = CycleSerializer


class CycleTimeSlotListAPIView(BaseTimeSlotListAPIView):
    serializer_class = ListCycleTimeSlotSerializer
    model_class = CycleTimeSlot
    machine_model_class = Cycle
    machine_fk_field = "cycle"


@swagger_auto_schema(
    request_body=BookCycleTimeSlotSerializer,
    responses={
        200: ListCycleTimeSlotSerializer(many=True),
        201: ListCycleTimeSlotSerializer(many=True),
    },
    operation_id="book_cycle_slot",
)
class CycleTimeSlotBookAPIView(BaseTimeSlotBookAPIView):
    queryset = CycleTimeSlot.objects.none()
    serializer_class = BookCycleTimeSlotSerializer
    list_serializer_class = ListCycleTimeSlotSerializer
    model_class = CycleTimeSlot
    machine_model_class = Cycle
    machine_fk_field = "cycle"
