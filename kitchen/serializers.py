from rest_framework import serializers
from .models import Induction, InductionTimeSlot
from django.utils import timezone
from datetime import timedelta


class InductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Induction
        fields = [
            "pk",
            "is_available",
        ]


class ListInductionTimeSlotSerializer(serializers.ModelSerializer):

    class Meta:
        model = InductionTimeSlot
        fields = [
            "pk",
            "induction",
            "is_booked",
            "start_time",
            "end_time",
            "booked_at",
        ]


class BookInductionTimeSlotSerializer(serializers.Serializer):
    start_time = serializers.DateTimeField(
        required=True,
    )

    def validate_start_time(self, value):
        """
        시작 시간 검증
        1. 시간대 정보 확인
        2. 30분 단위 확인 (0분 or 30분)
        3. 과거 시간 예약 방지 (1분 오차 허용)
        """
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone=timezone.get_default_timezone())

        now_aware = timezone.now()
        if value < now_aware - timedelta(minutes=1):
            raise serializers.ValidationError("과거 시간은 예약할 수 없습니다.")

        if value.minute not in [0, 30] or value.second != 0 or value.microsecond != 0:
            raise serializers.ValidationError(
                "시작 시간은 정시 또는 30분이어야 합니다."
            )

        return value
