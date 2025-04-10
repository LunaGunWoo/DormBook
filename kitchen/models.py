from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from users.models import User
from datetime import datetime, timedelta


class Induction(models.Model):
    is_available = models.BooleanField(
        "사용 가능 여부",
        default=True,
    )

    def __str__(self) -> str:
        return str(self.pk)


class InductionTimeSlot(models.Model):
    induction = models.ForeignKey(
        Induction,
        on_delete=models.CASCADE,
        verbose_name="인덕션",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="예약자",
    )
    start_time = models.DateTimeField("시작 시간")
    end_time = models.DateTimeField("종료 시간")
    booked_at = models.DateTimeField("예약 시간", null=True, blank=True)

    class Meta:
        ordering = ["start_time"]
        unique_together = ["induction", "start_time"]

    def __str__(self):
        status = "예약됨" if self.user else "가능"
        start_time_seoul = timezone.localtime(
            self.start_time, timezone=timezone.get_fixed_timezone(540)
        )
        return f"{self.induction} - {start_time_seoul.strftime('%Y-%m-%d %H:%M')} ({status})"

    @classmethod
    def create_time_slots(cls, days=7):
        start_date = timezone.localtime(
            timezone.now(), timezone=timezone.get_fixed_timezone(540)
        ).date()
        end_date = start_date + timedelta(days=days)

        open_at = 0
        close_at = 24
        unit_minute = 30

        for induction in Induction.objects.filter(is_available=True):
            current_date = start_date
            while current_date < end_date:
                current_time = timezone.make_aware(
                    datetime.combine(current_date, datetime.min.time()),
                    timezone=timezone.get_fixed_timezone(540),
                ) + timedelta(hours=open_at)

                end_time = timezone.make_aware(
                    datetime.combine(current_date, datetime.min.time()),
                    timezone=timezone.get_fixed_timezone(540),
                ) + timedelta(hours=close_at)

                while current_time < end_time:
                    slot_end_time = current_time + timedelta(minutes=unit_minute)
                    cls.objects.get_or_create(
                        induction=induction,
                        start_time=current_time,
                        end_time=slot_end_time,
                    )
                    current_time = slot_end_time

                current_date += timedelta(days=1)

    def book(self, user):
        if self.user:
            raise ValueError("이미 예약된 시간입니다.")
        self.user = user
        self.booked_at = timezone.now()
        self.save()

    @property
    def is_booked(self) -> bool:
        return True if self.user else False
