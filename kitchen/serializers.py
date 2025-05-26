from rest_framework import serializers
from .models import Induction, InductionTimeSlot
from django.utils import timezone
from datetime import datetime, timedelta

MAX_BOOKING_ACTIONS_PER_DAY = 3
SLOT_DURATION_MINUTES = 30


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
        read_only_fields = [
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
    duration_minutes = serializers.ChoiceField(
        choices=[SLOT_DURATION_MINUTES, SLOT_DURATION_MINUTES * 2],
        default=SLOT_DURATION_MINUTES,
        required=False,
        help_text="예약할 시간(30분 또는 60분) 선택",
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

    def validate(self, data):
        request = self.context.get("request")
        request_user = request.user

        start_time = data["start_time"]

        query_date = start_time.date()

        day_start = timezone.make_aware(
            datetime.combine(query_date, datetime.min.time()),
            timezone.get_default_timezone(),
        )
        day_end = day_start + timedelta(days=1)

        user_actions_count_today = (
            InductionTimeSlot.objects.filter(
                user=request_user,
                start_time__gte=day_start,
                start_time__lt=day_end,
            )
            .values("booked_at")
            .distinct()
            .count()
        )

        if user_actions_count_today >= MAX_BOOKING_ACTIONS_PER_DAY:
            raise serializers.ValidationError(
                f"하루에 최대 {MAX_BOOKING_ACTIONS_PER_DAY}번의 예약 행동만 가능합니다. "
                f"현재 {user_actions_count_today}번 예약하셨습니다."
            )

        return data
