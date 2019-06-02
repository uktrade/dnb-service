from django.core.management.base import BaseCommand

from company.elasticsearch import bulk_insert_companies, create_index
from company.models import Company


class Command(BaseCommand):
    help = 'Sync companies with elasticsearch'

    def add_arguments(self, parser):
        parser.add_argument('--rebuild-index', action='store_true', default=False)

    def handle(self, *args, **options):

        if options['rebuild_index']:
            self.stdout.write('Recreating index')
            create_index(delete_existing=True)

        success, failed = 0, 0

        companies = Company.objects.all()

        self.stdout.write('Syncing %d company records' % companies.count())

        for ok, item in bulk_insert_companies(companies):
            if ok:
                success += 1
            else:
                failed += 1
                self.stdout.write(self.style.ERROR('Failed: {}'.format(str(item))))

        self.stdout.write(self.style.SUCCESS(f'Done. Success: {success} Failed {failed}'))
