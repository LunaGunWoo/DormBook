from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.core.validators import RegexValidator


class CustomUserManager(BaseUserManager):
    def create_user(self, student_id_number, password=None):
        if not student_id_number:
            raise ValueError("학번은 꼭 있어야 합니다.")

        user = self.model(student_id_number=student_id_number)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, student_id_number, password=None):
        user = self.create_user(
            student_id_number=student_id_number,
            password=password,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin):
    objects = CustomUserManager()

    student_id_number = models.CharField(
        "학번",
        max_length=10,
        validators=[
            RegexValidator(
                regex=r"^\d{10}$",
                message="10자리 학번을 입력해주세요.",
            )
        ],
        unique=True,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "student_id_number"

    def __str__(self):
        return self.student_id_number
