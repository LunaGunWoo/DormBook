from django.core.validators import RegexValidator
from rest_framework import serializers
from lounge.serializers import (
    ListPingPongTableTimeSlotSerializer,
    ListArcadeMachineTimeSlotSerializer,
)
from kitchen.serializers import ListInductionTimeSlotSerializer
from gym.serializers import ListTreadmillTimeSlotSerializer, ListCycleTimeSlotSerializer


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class LoginSerializer(serializers.Serializer):
    student_id_number = serializers.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r"^\d{10}$",
                message="10자리 학번을 입력해주세요.",
            )
        ],
        required=True,
    )
    password = serializers.CharField(required=True)


class MyAllBookingsResponseSerializer(serializers.Serializer):
    ping_pong_table_bookings = ListPingPongTableTimeSlotSerializer(
        many=True, read_only=True, help_text="사용자의 탁구대 예약 목록"
    )
    arcade_machine_bookings = ListArcadeMachineTimeSlotSerializer(
        many=True, read_only=True, help_text="사용자의 아케이드 게임기 예약 목록"
    )
    induction_bookings = ListInductionTimeSlotSerializer(
        many=True, read_only=True, help_text="사용자의 인덕션 예약 목록"
    )
    treadmill_bookings = ListTreadmillTimeSlotSerializer(
        many=True, read_only=True, help_text="사용자의 런닝머신 예약 목록"
    )
    cycle_bookings = ListCycleTimeSlotSerializer(
        many=True, read_only=True, help_text="사용자의 사이클 예약 목록"
    )
