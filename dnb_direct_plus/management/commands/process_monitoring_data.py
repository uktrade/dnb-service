import logging
import os

from boto3 import client

from django.core.management.base import BaseCommand
from django.conf import settings

from dnb_direct_plus.monitoring import process_exception_file, process_seed_file, process_update_file

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

    def _delete_File(self, file_name):
        self.s3_client.detete_object(Bucket=settings.DNB_MONITORING_S3_BUCKET, Key=file_name)

    def handle(self, *args, **options):

        files = self._list_files()

        for file_name in files:

            if not file_name.startswith(settings.DNB_MONITORING_REGISTRATION_REFERENCE):
                self.stdout.write(f'Skipping {file_name} due to incorrect DNB monitoring reference')
                continue

            if 'HEADER' in file_name:
                continue

            if 'Exceptions' in file_name:
                handler = process_exception_file
            elif 'NOTIFICATION' in file_name:
                handler = process_update_file
            elif 'SEEDFILE' in file_name:
                handler = process_seed_file
            else:
                self.stdout.write(f'Skipping {file_name}')
                continue

            self.stdout.write(f'Processing {file_name}')

            bucket_path = os.path.join('s3://', settings.DNB_MONITORING_S3_BUCKET, file_name)

            try:
                handler(bucket_path)
            except BaseException as exc:
                self.stdout.write(f'An error occurred attempting to process {file_name}: {exc}')
            else:
                if settings.DNB_DELETE_PROCESSED_FILES:
                    self._delete_file(file_name)
