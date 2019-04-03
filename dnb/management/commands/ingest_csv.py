import logging
import time

from django.core.management.base import BaseCommand, CommandError

from dnb.ingest import ingest_csv


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import a DNB CSV data file'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str)

    def handle(self, *args, **options):
        start_time = time.time()

        try:
            with open(options['file'], 'rt', encoding='iso-8859-1') as fd:
                stats = ingest_csv(fd, logger)

        except IOError:
            raise CommandError('Cannot open file: {}'.format(options['file']))
        stats['time'] = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS('Took: {time}; imported: {processed}; failed: {failed}'.format(**stats)))
