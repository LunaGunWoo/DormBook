from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import (
    PingPongTable,
    PingPongTableTimeSlot,
    ArcadeMachine,
    ArcadeMachineTimeSlot,
)
from .serializers import (
    PingPongTableSerializer,
    ListPingPongTableTimeSlotSerializer,
    BookPingPongTableTimeSlotSerializer,
    PING_PONG_SLOT_DURATION_MINUTES,
    ArcadeMachineSerializer,
    ListArcadeMachineTimeSlotSerializer,
    BookArcadeMachineTimeSlotSerializer,
    ARCADE_MACHINE_SLOT_DURATION_MINUTES,
)
from datetime import datetime, timedelta


class PingPongTableListAPIView(generics.ListAPIView):
    queryset = PingPongTable.objects.all()
    serializer_class = PingPongTableSerializer
    permission_classes = [permissions.IsAuthenticated]


class PingPongTableTimeSlotListAPIView(generics.ListAPIView):
    serializer_class = ListPingPongTableTimeSlotSerializer
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
                return PingPongTableTimeSlot.objects.none()
        ping_pong_table_pk = self.kwargs.get("pk")
        date_str = self.request.query_params.get("date")
        if not date_str:
            raise ValidationError("날짜를 지정해주세요.")
        try:
            query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("날짜 형식이 잘못되었습니다. (YYYY-MM-DD)")
        start_dt = timezone.make_aware(
            datetime.combine(query_date, datetime.min.time()),
            timezone.get_default_timezone(),
        )
        end_dt = start_dt + timedelta(days=1)
        queryset = PingPongTableTimeSlot.objects.filter(
            ping_pong_table__pk=ping_pong_table_pk,
            start_time__gte=start_dt,
            start_time__lt=end_dt,
            user__isnull=False,
        ).select_related("user", "ping_pong_table")
        return queryset


class PingPongTableTimeSlotBookAPIView(generics.GenericAPIView):
    queryset = PingPongTableTimeSlot.objects.none()
    serializer_class = BookPingPongTableTimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        return {"request": self.request, "format": self.format_kwarg, "view": self}

    @swagger_auto_schema(
        request_body=BookPingPongTableTimeSlotSerializer,
        responses={
            200: openapi.Response(
                "기존 슬롯 예약 성공", ListPingPongTableTimeSlotSerializer(many=True)
            ),
            201: openapi.Response(
                "새 슬롯 생성 및 예약 성공",
                ListPingPongTableTimeSlotSerializer(many=True),
            ),
            400: "잘못된 요청",
            404: "탁구대를 찾을 수 없음",
            409: "동시 예약 시도 충돌 또는 이미 예약된 슬롯",
            500: "서버 내부 오류",
        },
        operation_description=f"탁구대 특정 시간 슬롯 예약. {PING_PONG_SLOT_DURATION_MINUTES}분 또는 {PING_PONG_SLOT_DURATION_MINUTES*2}분 단위. 하루 최대 1번 예약 가능.",
    )
    def post(self, request, pk):
        ping_pong_table = get_object_or_404(PingPongTable, pk=pk)
        if not ping_pong_table.is_available:
            return Response(
                {"error": "사용 불가능한 탁구대입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        start_time = serializer.validated_data["start_time"]
        duration_minutes = serializer.validated_data.get(
            "duration_minutes", PING_PONG_SLOT_DURATION_MINUTES
        )
        num_slots_to_book = duration_minutes // PING_PONG_SLOT_DURATION_MINUTES
        booked_slot_objects = []
        any_slot_newly_created_in_db = False
        timestamp_for_this_booking_action = timezone.now()
        try:
            with transaction.atomic():
                for i in range(num_slots_to_book):
                    current_slot_start_time = start_time + timedelta(
                        minutes=i * PING_PONG_SLOT_DURATION_MINUTES
                    )
                    current_slot_end_time = current_slot_start_time + timedelta(
                        minutes=PING_PONG_SLOT_DURATION_MINUTES
                    )
                    (
                        slot,
                        created,
                    ) = PingPongTableTimeSlot.objects.select_for_update().get_or_create(
                        ping_pong_table=ping_pong_table,
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
                                f"{current_slot_start_time.strftime('%H:%M')} 슬롯은 이미 본인의 이전 예약에 포함되어 있습니다."
                            )
                        else:
                            raise ValueError(
                                f"{current_slot_start_time.strftime('%H:%M')} 슬롯은 이미 다른 사용자가 예약했습니다."
                            )
            response_serializer = ListPingPongTableTimeSlotSerializer(
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
            return Response(
                {"error": "예약 처리 중 예측하지 못한 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ArcadeMachineListAPIView(generics.ListAPIView):
    queryset = ArcadeMachine.objects.all()
    serializer_class = ArcadeMachineSerializer
    permission_classes = [permissions.IsAuthenticated]


class ArcadeMachineTimeSlotListAPIView(generics.ListAPIView):
    serializer_class = ListArcadeMachineTimeSlotSerializer
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
                return ArcadeMachineTimeSlot.objects.none()

        arcade_machine_pk = self.kwargs.get("pk")
        date_str = self.request.query_params.get("date")
        if not date_str:
            raise ValidationError("날짜를 지정해주세요.")
        try:
            query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("날짜 형식이 잘못되었습니다. (YYYY-MM-DD)")

        start_dt = timezone.make_aware(
            datetime.combine(query_date, datetime.min.time()),
            timezone.get_default_timezone(),
        )
        end_dt = start_dt + timedelta(days=1)

        queryset = ArcadeMachineTimeSlot.objects.filter(
            arcade_machine__pk=arcade_machine_pk,
            start_time__gte=start_dt,
            start_time__lt=end_dt,
            user__isnull=False,
        ).select_related("user", "arcade_machine")
        return queryset


class ArcadeMachineTimeSlotBookAPIView(generics.GenericAPIView):
    queryset = ArcadeMachineTimeSlot.objects.none()
    serializer_class = BookArcadeMachineTimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        return {"request": self.request, "format": self.format_kwarg, "view": self}

    @swagger_auto_schema(
        request_body=BookArcadeMachineTimeSlotSerializer,
        responses={
            200: openapi.Response(
                "기존 슬롯 예약 성공", ListArcadeMachineTimeSlotSerializer(many=True)
            ),
            201: openapi.Response(
                "새 슬롯 생성 및 예약 성공",
                ListArcadeMachineTimeSlotSerializer(many=True),
            ),
            400: "잘못된 요청",
            404: "아케이드 머신을 찾을 수 없음",
            409: "동시 예약 시도 충돌 또는 이미 예약된 슬롯",
            500: "서버 내부 오류",
        },
        operation_description=f"아케이드 머신 특정 시간 슬롯 예약. {ARCADE_MACHINE_SLOT_DURATION_MINUTES}분 또는 {ARCADE_MACHINE_SLOT_DURATION_MINUTES*2}분 단위. 하루 최대 1번 예약 가능.",
    )
    def post(self, request, pk):
        arcade_machine = get_object_or_404(ArcadeMachine, pk=pk)
        if not arcade_machine.is_available:
            return Response(
                {"error": "사용 불가능한 아케이드 머신입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        start_time = serializer.validated_data["start_time"]
        duration_minutes = serializer.validated_data.get(
            "duration_minutes", ARCADE_MACHINE_SLOT_DURATION_MINUTES
        )
        num_slots_to_book = duration_minutes // ARCADE_MACHINE_SLOT_DURATION_MINUTES

        booked_slot_objects = []
        any_slot_newly_created_in_db = False
        timestamp_for_this_booking_action = timezone.now()

        try:
            with transaction.atomic():
                for i in range(num_slots_to_book):
                    current_slot_start_time = start_time + timedelta(
                        minutes=i * ARCADE_MACHINE_SLOT_DURATION_MINUTES
                    )
                    current_slot_end_time = current_slot_start_time + timedelta(
                        minutes=ARCADE_MACHINE_SLOT_DURATION_MINUTES
                    )

                    (
                        slot,
                        created,
                    ) = ArcadeMachineTimeSlot.objects.select_for_update().get_or_create(
                        arcade_machine=arcade_machine,
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
                                f"{current_slot_start_time.strftime('%H:%M')} 슬롯은 이미 본인의 이전 예약에 포함되어 있습니다."
                            )
                        else:
                            raise ValueError(
                                f"{current_slot_start_time.strftime('%H:%M')} 슬롯은 이미 다른 사용자가 예약했습니다."
                            )

            response_serializer = ListArcadeMachineTimeSlotSerializer(
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
            return Response(
                {"error": "예약 처리 중 예측하지 못한 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
