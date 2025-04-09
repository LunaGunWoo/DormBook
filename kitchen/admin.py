from django.contrib import admin
from .models import Induction, InductionTimeSlot


@admin.action(description="사용 가능 여부 바꾸기")
def change_is_available(modeladmin, request, inductions):
    for induction in inductions.all():
        induction.is_available = not induction.is_available
        induction.save()


@admin.register(Induction)
class InductionAdmin(admin.ModelAdmin):

    actions = [
        change_is_available,
    ]

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
