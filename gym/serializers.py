from rest_framework import serializers
from .models import Treadmill, TreadmillTimeSlot, Cycle, CycleTimeSlot
from django.utils import timezone
from datetime import datetime, timedelta


MAX_BOOKING_ACTIONS_PER_DAY_GYM = 2
SLOT_DURATION_MINUTES_GYM = 30


class BaseMachineSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            "pk",
            "is_using",
            "is_available",
        ]


class BaseListTimeSlotSerializer(serializers.ModelSerializer):

    is_booked = serializers.BooleanField(read_only=True)

    class Meta:
        fields = [
            "pk",
            "is_booked",
            "start_time",
            "end_time",
            "booked_at",
        ]
        read_only_fields = fields


class BaseBookTimeSlotSerializer(serializers.Serializer):
    start_time = serializers.DateTimeField(required=True)
    duration_minutes = serializers.ChoiceField(
        choices=[
            SLOT_DURATION_MINUTES_GYM,
            SLOT_DURATION_MINUTES_GYM * 2,
        ],
        default=SLOT_DURATION_MINUTES_GYM,
        required=False,
        help_text=f"예약할 시간 ({SLOT_DURATION_MINUTES_GYM}분 또는 {SLOT_DURATION_MINUTES_GYM * 2}분) 선택",
    )

    timeslot_model = None

    def validate_start_time(self, value):
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_default_timezone())
        now_aware = timezone.now()
        if value < now_aware - timedelta(minutes=1):
            raise serializers.ValidationError("과거 시간은 예약할 수 없습니다.")
        if value.minute not in [0, 30] or value.second != 0 or value.microsecond != 0:
            raise serializers.ValidationError(
                "시작 시간은 매 시 정각 또는 30분이어야 합니다."
            )
        return value

    def validate(self, data):
        request = self.context.get("request")
        if not request or not hasattr(request, "user"):
            raise serializers.ValidationError("요청 컨텍스트에 사용자가 없습니다.")

        if not self.timeslot_model:
            raise serializers.ValidationError(
                "Serializer에 timeslot_model이 설정되지 않았습니다."
            )

        request_user = request.user
        start_time = data["start_time"]
        query_date = start_time.date()
        day_start = timezone.make_aware(
            datetime.combine(query_date, datetime.min.time()),
            timezone.get_default_timezone(),
        )
        day_end = day_start + timedelta(days=1)

        user_actions_count_today = (
            self.timeslot_model.objects.filter(
                user=request_user,
                booked_at__gte=day_start,
                booked_at__lt=day_end,
            )
            .values("booked_at")
            .distinct()
            .count()
        )

        if user_actions_count_today >= MAX_BOOKING_ACTIONS_PER_DAY_GYM:
            raise serializers.ValidationError(
                f"하루에 최대 {MAX_BOOKING_ACTIONS_PER_DAY_GYM}번의 예약 행동만 가능합니다. "
                f"이미 {user_actions_count_today}번 예약하셨습니다."
            )
        return data


class TreadmillSerializer(BaseMachineSerializer):
    class Meta(BaseMachineSerializer.Meta):
        model = Treadmill


class ListTreadmillTimeSlotSerializer(BaseListTimeSlotSerializer):
    treadmill = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta(BaseListTimeSlotSerializer.Meta):
        model = TreadmillTimeSlot
        fields = BaseListTimeSlotSerializer.Meta.fields + ["treadmill"]
        read_only_fields = fields


class BookTreadmillTimeSlotSerializer(BaseBookTimeSlotSerializer):
    pass


class CycleSerializer(BaseMachineSerializer):
    class Meta(BaseMachineSerializer.Meta):
        model = Cycle


class ListCycleTimeSlotSerializer(BaseListTimeSlotSerializer):
    cycle = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta(BaseListTimeSlotSerializer.Meta):
        model = CycleTimeSlot
        fields = BaseListTimeSlotSerializer.Meta.fields + ["cycle"]
        read_only_fields = fields


class BookCycleTimeSlotSerializer(BaseBookTimeSlotSerializer):
    pass
