from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "student_id_number",
                    "password",
                )
            },
        ),
        (
            ("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (("Important dates"), {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": (
                    "wide",
                    "extrapretty",
                ),
                "fields": (
                    "student_id_number",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
    list_display = ("student_id_number", "is_staff")
    ordering = ("student_id_number",)
