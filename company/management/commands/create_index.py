from django.core.management.base import BaseCommand

from company.elasticsearch import create_index


class Command(BaseCommand):
    help = 'Sync companies with elasticsearch'

    def add_arguments(self, parser):
        parser.add_argument('--delete-index', action='store_true', default=False)

    def handle(self, *args, **options):

        create_index(delete_existing=options['delete_index'])

        self.stdout.write(self.style.SUCCESS('Done.'))
