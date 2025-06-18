from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Brigade, User, Worker, WorkRecord


class UserAdmin(BaseUserAdmin):
    list_display = ("username", "is_staff", "is_superuser")
    list_filter = ("is_staff", "is_superuser")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password"),
            },
        ),
    )
    search_fields = ("username",)
    ordering = ("username",)


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ("__str__", "hourly_rate", "is_foreman", "user")
    list_filter = ("is_foreman",)
    search_fields = ("first_name", "last_name")


@admin.register(Brigade)
class BrigadeAdmin(admin.ModelAdmin):
    list_display = ("__str__", "foreman")
    search_fields = (
        "foreman__username",
        "foreman__worker__first_name",
        "foreman__worker__last_name",
    )


@admin.register(WorkRecord)
class WorkRecordAdmin(admin.ModelAdmin):
    list_display = ("worker", "date", "hours")
    list_filter = ("date", "worker")


admin.site.register(User, UserAdmin)
