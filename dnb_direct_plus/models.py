from django.db import models


class MonitoringFileRecord(models.Model):
    """This model is used to track which monitoring update files have been ingested
    to avoid ingesting the same file twice."""
    timestamp = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=255, unique=True)
    total = models.PositiveIntegerField()
    failed = models.PositiveIntegerField()

    def __str__(self):
        return self.file_name
