from django.contrib import admin

from .models import MonitoringFileRecord


@admin.register(MonitoringFileRecord)
class MonitoringFileRecordAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'file_name', 'total', 'failed')
