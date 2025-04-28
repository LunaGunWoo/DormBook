from django.contrib import admin
from .models import PingPongTable


@admin.action(description="사용 가능 여부 바꾸기")
def change_is_available(modeladmin, request, pingPongTables):
    for pingPongTable in pingPongTables.all():
        pingPongTable.is_available = not pingPongTable.is_available
        pingPongTable.save()


@admin.register(PingPongTable)
class PingPongTableAdmin(admin.ModelAdmin):

    actions = [change_is_available]

    list_display = (
        "pk",
        "is_available",
    )
