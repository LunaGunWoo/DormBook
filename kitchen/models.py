from django.db import models


class Induction(models.Model):
    is_available = models.BooleanField(
        "사용 가능 여부",
        default=True,
    )
    is_free_use = models.BooleanField(
        "자유 사용",
        default=False,
    )

    def __str__(self) -> str:
        return str(self.pk)
