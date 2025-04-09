from rest_framework import serializers
from .models import Induction, InductionTimeSlot


class InductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Induction
        fields = [
            "pk",
            "is_available",
        ]


class ListInductionTimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = InductionTimeSlot
        fields = [
            "pk",
            "is_booked",
            "start_time",
            "end_time",
        ]


class BookInductionTimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = InductionTimeSlot
        fields = []
