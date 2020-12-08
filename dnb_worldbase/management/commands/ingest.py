import datetime
import logging
import time

from boto3 import client

from django.conf import settings
from django.core.management.base import BaseCommand

from dnb_worldbase.ingest import process_wb_file

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import a DNB Worldbase CSV data file'

    s3_client = None

    def __init__(self):
        self.s3_client = client('s3')

        super().__init__()

    def _list_files(self, path=None):
        return [
            item['Key'] for item in
            self.s3_client.list_objects_v2(
                Bucket=settings.DNB_MONITORING_S3_BUCKET,
                Prefix=path
            ).get('Contents', [])
        ]

    def add_arguments(self, parser):
        parser.add_argument('--creation-date', type=datetime.datetime.fromisoformat)
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--file', type=str)
        group.add_argument('--s3-bucket-path', type=str)

    def handle(self, *args, **options):

        start_time = time.time()

        if options['s3_bucket_path']:
            files = [
                f's3://{settings.DNB_MONITORING_S3_BUCKET}/{file_}'
                for file_ in self._list_files(path=options['s3_bucket_path'])
            ]
        else:
            files = [options['file']]

        for file_path in files:
            self.stdout.write(f'Processing file: {file_path}')

            try:
                stats = process_wb_file(file_path, options['creation_date'])
            except BaseException:  # noqa
                logger.exception(f'An error occurred processing file {file_path}')
            else:
                self.stdout.write('Created: {created}; updated: {updated}; failed: {failed}'.format(**stats))

        total_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(f'Took: {total_time}'))
