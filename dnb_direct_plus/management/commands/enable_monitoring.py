import logging

from django.core.management.base import BaseCommand

from dnb_direct_plus.monitoring import add_companies_to_monitoring_registration

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Retrieve and process files from the DNB monitoring S3 bucket'

    def handle(self, *args, **options):

        total = add_companies_to_monitoring_registration()

        self.stdout.write(f'{total} companies added to monitoring registration')
