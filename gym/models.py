from django.db import models
from django.utils import timezone
from users.models import User


class Machine(models.Model):
    """
    공통적인 기계 특성을 위한 추상 기본 모델
    """

    is_available = models.BooleanField(
        "사용 가능 여부",
        default=True,
    )

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.pk


class TimeSlot(models.Model):
    """
    공통적인 타임슬롯 특성을 위한 추상 기본 모델
    """

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="예약자",
    )
    start_time = models.DateTimeField("시작 시간")
    end_time = models.DateTimeField("종료 시간")
    booked_at = models.DateTimeField("예약 확정 시간", null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ["start_time"]

    @property
    def is_booked(self) -> bool:
        return self.user is not None


class Treadmill(Machine):
    @property
    def is_using(self) -> bool:
        now = timezone.now()
        return TreadmillTimeSlot.objects.filter(
            treadmill=self, start_time__lte=now, end_time__gt=now, user__isnull=False
        ).exists()


class TreadmillTimeSlot(TimeSlot):
    treadmill = models.ForeignKey(
        Treadmill,
        on_delete=models.CASCADE,
        verbose_name="런닝머신",
    )

    class Meta(TimeSlot.Meta):
        unique_together = ["treadmill", "start_time"]

    def __str__(self):
        status = "Booked" if self.user else "Available"
        try:
            start_time_seoul = timezone.localtime(
                self.start_time,
                timezone=timezone.get_fixed_timezone(540),
            )
            user_info = f" by {self.user.student_id_number}" if self.user else ""
            return f"{self.treadmill} - {start_time_seoul.strftime('%Y-%m-%d %H:%M')} ({status}{user_info})"
        except AttributeError:
            return f"TreadmillTimeSlot object (Incomplete)"


class Cycle(Machine):
    @property
    def is_using(self) -> bool:
        now = timezone.now()
        return CycleTimeSlot.objects.filter(
            cycle=self,
            start_time__lte=now,
            end_time__gt=now,
            user__isnull=False,
        ).exists()


class CycleTimeSlot(TimeSlot):
    cycle = models.ForeignKey(
        Cycle,
        on_delete=models.CASCADE,
        verbose_name="사이클",
    )

    class Meta(TimeSlot.Meta):
        unique_together = ["cycle", "start_time"]

    def __str__(self):
        status = "Booked" if self.user else "Available"
        try:
            start_time_seoul = timezone.localtime(
                self.start_time,
                timezone=timezone.get_fixed_timezone(540),
            )
            user_info = f" by {self.user.student_id_number}" if self.user else ""
            return f"{self.cycle} - {start_time_seoul.strftime('%Y-%m-%d %H:%M')} ({status}{user_info})"
        except AttributeError:
            return f"CycleTimeSlot object (Incomplete)"
