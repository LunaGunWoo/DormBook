from django.contrib import admin
from django.http import HttpRequest
from .models import Induction, InductionTimeSlot


@admin.action(description="사용 가능 여부 바꾸기")
def change_is_available(modeladmin, request, inductions):
    for induction in inductions.all():
        induction.is_available = not induction.is_available
        induction.save()


@admin.register(Induction)
class InductionAdmin(admin.ModelAdmin):

    actions = [change_is_available]

    list_display = (
        "pk",
        "is_available",
    )


class IsBookedFilter(admin.SimpleListFilter):
    title = "예약됨 여부로"
    parameter_name = "is_booked"

    def lookups(self, request, model_admin):
        return [
            ("true", "예"),
            ("false", "아니오"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "true":
            return queryset.filter(user__isnull=False)
        if self.value() == "false":
            return queryset.filter(user__isnull=True)


@admin.register(InductionTimeSlot)
class InductionTimeSlotAdmin(admin.ModelAdmin):
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    list_filter = [
        IsBookedFilter,
        "induction",
    ]
    readonly_fields = (
        "start_time",
        "end_time",
        "booked_at",
    )
