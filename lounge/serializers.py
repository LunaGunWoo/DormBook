from rest_framework import serializers
from .models import PingPongTable


class PingPongTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = PingPongTable
        fields = [
            "pk",
            "is_available",
        ]
