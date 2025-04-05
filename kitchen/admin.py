from django.contrib import admin
from .models import Induction


@admin.register(Induction)
class InductionAdmin(admin.ModelAdmin):
    pass
