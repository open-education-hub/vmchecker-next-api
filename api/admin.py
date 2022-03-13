from django.contrib import admin

from api.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["__str__", "state"]
    list_filter = ["state"]
    readonly_fields = ["error_info"]
