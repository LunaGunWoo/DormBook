from django.contrib import admin
from .models import Induction


@admin.register(Induction)
class InductionAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "is_available",
        "is_free_use",
    )
