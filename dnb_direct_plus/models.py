from django.db import models


class MonitoringFileRecord(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=255)
    total = models.PositiveIntegerField()
    failed = models.PositiveIntegerField()

    def __str__(self):
        return self.file_name
