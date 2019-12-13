import logging
import os

from boto3 import client

from django.core.management.base import BaseCommand
from django.conf import settings

from dnb_direct_plus.models import MonitoringFileRecord
from dnb_direct_plus.monitoring import process_exception_file, process_notification_file

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Retrieve and process files from the DNB monitoring S3 bucket'

    s3_client = None

    def __init__(self):
        self.s3_client = client('s3')

        super().__init__()

    def _list_files(self):
        return [
            item['Key'] for item in
            self.s3_client.list_objects(Bucket=settings.DNB_MONITORING_S3_BUCKET)['Contents']
        ]

    def _archive_file(self, file_name):
        self.s3_client.Object(settings.DNB_MONITORING_S3_BUCKET, os.path.join(settings.DNB_ARCHIVE_PATH, file_name)) \
            .copy_from(CopySource=settings.DNB_MONITORING_S3_BUCKET + '/' + file_name)
        self.s3_client.Object(settings.DNB_MONITORING_S3_BUCKET, file_name).delete()

    def handle(self, *args, **options):
        files = self._list_files()

        summary = []

        for file_name in files:

            if not file_name.startswith(settings.DNB_MONITORING_REGISTRATION_REFERENCE):
                # file does not relate to the monitoring registration
                continue

            if 'HEADER' in file_name:
                continue

            if file_name.startswith(settings.DNB_ARCHIVE_PATH):
                continue

            if MonitoringFileRecord.objects.filter(file_name=file_name).exists():
                self.stdout.write(f'{file_name} already processed; skipping')
                continue

            if 'Exceptions' in file_name:
                handler = process_exception_file
            elif 'NOTIFICATION' in file_name or 'SEEDFILE' in file_name:
                handler = process_notification_file
            else:
                continue

            bucket_path = os.path.join('s3://', settings.DNB_MONITORING_S3_BUCKET, file_name)

            self.stdout.write(f'Processing: {file_name}')

            total, total_success = handler(bucket_path)

            summary.append(
                dict(file=file_name, total=total, failed=total - total_success)
            )
            MonitoringFileRecord.objects.create(
                file_name=file_name, total=total, failed=total - total_success)

            if settings.DNB_ARCHIVE_PROCESSED_FILES:
                self._archive_file(file_name)

        summary_text = '\n'.join(
            '{file}\t\tTotal: {total}\tFailed: {failed}'.format(**line) for line in summary)

        if summary_text:
            self.stdout.write(summary_text)
