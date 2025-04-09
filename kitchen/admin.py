from django.contrib import admin
from .models import Induction, InductionTimeSlot


@admin.register(Induction)
class InductionAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "is_available",
    )


@admin.register(InductionTimeSlot)
class InductionTimeSlotAdmin(admin.ModelAdmin):
    list_filter = [
        "induction",
        "start_time",
    ]
