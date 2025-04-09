from rest_framework import serializers
from .models import Induction


class InductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Induction
        fields = [
            "pk",
            "is_available",
        ]
