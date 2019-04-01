import csv
import time
import logging

from django.core.management.base import BaseCommand, CommandError

from dnb.ingest import CompanyResource, ValidationError


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import a DNB CSV data file'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str)

    def handle(self, *args, **options):
        start_time = time.time()

        try:
            with open(options['file'], 'rt', encoding='iso-8859-1') as fd:
                csv_reader = csv.reader(fd)

                heading = []
                for row_number, row in enumerate(csv_reader, 1):
                    assert len(row) == 112, f'incorrect number of rows on line {row_number}'

                    if not heading:
                        heading = row
                        continue

                    try:
                        company = CompanyResource(row)
                    except ValidationError as exc:
                        logging.exception(f'Unable to process row {row_number}; raw data: {row}')
                        continue

                    try:
                        _, company_obj = company.get_or_create()
                    except:
                        print(company.data)
                        raise

        except IOError:
            raise CommandError('Unable to open file: {}'.format(options['file']))

        self.stdout.write(self.style.SUCCESS('Took: {}'.format(time.time() - start_time)))
