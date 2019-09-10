import logging
import time

from django.core.management.base import BaseCommand, CommandError
from smart_open import open

from dnb_worldbase.ingest import process_file

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import a DNB Worldbase CSV data file'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str)

    def handle(self, *args, **options):
        start_time = time.time()

        try:
            with open(options['file'], 'rt', encoding='iso-8859-1') as wb_file:
                stats = process_file(wb_file)

        except IOError:
            raise CommandError('Cannot open file: {}'.format(options['file']))

        stats['time'] = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                'Took: {time}; created: {created}; updated: {updated}; failed: {failed}'.format(**stats)))
