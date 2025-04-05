from django.core.validators import RegexValidator
from rest_framework import serializers


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
