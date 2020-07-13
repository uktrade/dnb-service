import os

from django.conf import settings
from django.core.management.base import BaseCommand

from company.models import InvestigationRequest

class Command(BaseCommand):
    def handle(self, *args, **options):

        faulty_string = '\u0003'
        records = InvestigationRequest.objects.all()

        for record in records:
            if faulty_string in record.company_details['telephone']:
                details = record.company_details
                details['telephone'] = details['telephone'].replace(faulty_string, '')

                record.company_details = details
                record.save()
