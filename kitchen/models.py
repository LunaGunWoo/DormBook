from django.db import models


class Induction(models.Model):
    is_available = models.BooleanField(
        "사용 가능 여부",
        default=True,
    )

    def __str__(self) -> str:
        return self.pk
