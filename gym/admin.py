from django.contrib import admin
from django.http import HttpRequest
from .models import Treadmill, TreadmillTimeSlot, Cycle, CycleTimeSlot


@admin.action(description="선택된 항목의 사용 가능 여부 반전")
def toggle_availability(modeladmin, request, queryset):
    for obj in queryset:
        obj.is_available = not obj.is_available
        obj.save()


class MachineAdmin(admin.ModelAdmin):
    actions = [toggle_availability]
    list_display = (
        "name",
        "is_available",
    )
    search_fields = ("name",)


class TimeSlotAdmin(admin.ModelAdmin):
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    list_filter = [
        ("user", admin.EmptyFieldListFilter),
    ]
    readonly_fields = (
        "user",
        "start_time",
        "end_time",
        "booked_at",
    )
    search_fields = ("user__student_id_number",)

    def get_list_display(self, request):

        base_display = (
            "__str__",
            "user",
            "start_time",
            "end_time",
            "is_booked",
        )
        if hasattr(self.model, "treadmill"):
            return base_display + ("treadmill",)
        elif hasattr(self.model, "cycle"):
            return base_display + ("cycle",)
        return base_display


@admin.register(Treadmill)
class TreadmillAdmin(MachineAdmin):
    pass


@admin.register(TreadmillTimeSlot)
class TreadmillTimeSlotAdmin(TimeSlotAdmin):
    list_filter = TimeSlotAdmin.list_filter + ["treadmill"]
    search_fields = TimeSlotAdmin.search_fields + ("treadmill__name",)


@admin.register(Cycle)
class CycleAdmin(MachineAdmin):
    pass


@admin.register(CycleTimeSlot)
class CycleTimeSlotAdmin(TimeSlotAdmin):
    list_filter = TimeSlotAdmin.list_filter + ["cycle"]
    search_fields = TimeSlotAdmin.search_fields + ("cycle__name",)
