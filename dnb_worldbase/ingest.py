import csv
import logging

from django.db import transaction
from django.utils import timezone

from company.models import Company, Country, PrimaryIndustryCode, RegistrationNumber

from .constants import WB_HEADER_FIELDS
from .mapping import extract_company_data


logger = logging.getLogger(__name__)


@transaction.atomic
def update_company(wb_data):
    """
    Update company with worldbase data
    """
    foreign_key_fields = ['registration_numbers', 'primary_industry_codes', 'industry_codes']

    company_data = extract_company_data(wb_data)

    try:
        company = Company.objects.get(duns_number=company_data['duns_number'])
    except Company.DoesNotExist:
        company = Company()

    created = company.pk is None

    overwrite_fields = created or not company.source

    company.worldbase_source_updated_timestamp = timezone.now()
    company.worldbase_source = wb_data

    if overwrite_fields:
        for field, value in company_data.items():
            if field.endswith('country'):
                setattr(company, field, Country.objects.get(iso_alpha2=value))
            elif field not in foreign_key_fields:
                setattr(company, field, value)

    company.save()

    if overwrite_fields:
        # Can't delete records before company is saved.
        company.registration_numbers.all().delete()
        company.primary_industry_codes.all().delete()

    company.save()

    if overwrite_fields:
        for registration_number in company_data['registration_numbers']:
            RegistrationNumber.objects.create(
                company=company,
                registration_type=registration_number['registration_type'],
                registration_number=registration_number['registration_number'],
            )
        for primary_industry_code in company_data['primary_industry_codes']:
            PrimaryIndustryCode.objects.create(
                company=company,
                code=primary_industry_code['code'],
                description=primary_industry_code['description'],
            )

    return created


def process_file(wb_file):
    """Parse a Worldbase file and import into the database"""

    csv_reader = csv.reader(wb_file, quotechar='"')

    stats = {
        'created': 0,
        'updated': 0,
        'failed': 0,
    }

    for row_number, row_data in enumerate(csv_reader, 1):

        if row_number == 1:
            continue

        wb_data = dict(zip(WB_HEADER_FIELDS, row_data))

        try:
            created = update_company(wb_data)
        except BaseException as ex:
            logger.warning(f'row {row_number} failed {ex}')

            stats['failed'] += 1
        else:
            if created:
                stats['created'] += 1
            else:
                stats['updated'] += 1

    return stats
