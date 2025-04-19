from django.db import models
from django.utils import timezone
from users.models import User


class Induction(models.Model):
    is_available = models.BooleanField(
        "사용 가능 여부",
        default=True,
    )

    def __str__(self) -> str:
        return f"Induction {self.pk}"


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
        status = "Booked" if self.user else "Available (Created)"
        try:
            start_time_seoul = timezone.localtime(
                self.start_time, timezone=timezone.get_fixed_timezone(540),
            )
            user_info = f" by {self.user.student_id_number}" if self.user else ""
            return f"{self.induction} - {start_time_seoul.strftime('%Y-%m-%d %H:%M')} ({status}{user_info})"
        except AttributeError:
            return f"InductionTimeSlot object (Incomplete)"

    def book(self, user):
        if self.user:
            raise ValueError("이미 예약된 시간입니다.")
        self.user = user
        self.booked_at = timezone.now()
        self.save()

    @property
    def is_booked(self) -> bool:
        return self.user is not None
