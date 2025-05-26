from django.contrib import admin
from django.http import HttpRequest
from .models import (
    PingPongTable,
    PingPongTableTimeSlot,
    ArcadeMachine,
    ArcadeMachineTimeSlot,
)


@admin.action(description="사용 가능 여부 바꾸기")
def change_is_available(modeladmin, request, objects):
    for object in objects.all():
        object.is_available = not object.is_available
        object.save()


@admin.register(PingPongTable)
class PingPongTableAdmin(admin.ModelAdmin):

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


@admin.register(PingPongTableTimeSlot)
class PingPongTableTimeSlotAdmin(admin.ModelAdmin):
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    list_filter = [
        IsBookedFilter,
        "ping_pong_table",
    ]
    readonly_fields = (
        "start_time",
        "end_time",
        "booked_at",
    )


@admin.register(ArcadeMachine)
class ArcadeMachineAdmin(admin.ModelAdmin):
    actions = [change_is_available]
    list_display = (
        "pk",
        "is_available",
    )


@admin.register(ArcadeMachineTimeSlot)
class ArcadeMachineTimeSlotAdmin(admin.ModelAdmin):
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    list_filter = [
        IsBookedFilter,
        "arcade_machine",
    ]
    readonly_fields = (
        "user",
        "start_time",
        "end_time",
        "booked_at",
    )
    list_display = (
        "__str__",
        "arcade_machine",
        "user",
        "start_time",
        "end_time",
        "is_booked",
    )
    search_fields = ("user__student_id_number",)
