import csv
import logging

from django.db import transaction

from company.forms import CompanyValidationForm, RegistrationNumberValidationForm
from company.models import Company

from .constants import WB_FILE_COLUMN_COUNT, WB_HEADER_FIELDS
from .mapping import extract_company_data

logger = logging.getLogger(__name__)


@transaction.atomic
def validate_and_save_company(company_data):
    """Validate, then create or update the company data

    Returns a tuple (success, created, errors)

    success: boolean; was the transaction successful?
    created: boolean; True if the company was created, False if it was updated. Only relevant if success=True
    errors: a list of field errors. Only relevant if success=False
    """

    company_data['last_updated_source'] = source.name

    try:
        company_instance = Company.objects.get(duns_number=company_data['duns_number'])
    except Company.DoesNotExist:
        company_instance = None

    is_created = not company_instance

    registration_numbers = company_data.pop('registration_numbers', [])

    registration_number_forms = [RegistrationNumberValidationForm(item) for item in registration_numbers]

    company_form = CompanyValidationForm(company_data, instance=company_instance)

    if company_form.is_valid() and all(form.is_valid() for form in registration_number_forms):

        if company_instance:
            company_instance.registrationnumber_set.all().delete()

        company = company_form.save()

        for form in registration_number_forms:
            registration_number = form.save(commit=False)
            registration_number.company = company
            registration_number.save()

        return True, is_created, None
    else:
        form_errors = [form.errors for form in [company_form] + registration_number_forms if not form.is_valid()]

        return False, None, form_errors


def process_file(wb_file):
    """Parse a Worldbase file and import into the database"""

    csv_reader = csv.reader(wb_file)

    stats = {
        'created': 0,
        'updated': 0,
        'failed': 0,
    }

    for row_number, row_data in enumerate(csv_reader, 1):

        assert len(row_data) == WB_FILE_COLUMN_COUNT, f'incorrect number of columns on line {row_number}'

        if row_number == 1:
            assert row_data == WB_HEADER_FIELDS, 'CSV column headings do not match expected values'
            continue

        wb_data = dict(zip(WB_HEADER_FIELDS, row_data))

        try:
            company_data = extract_company_data(wb_data)
        except BaseException:
            logger.exception(f'row {row_number} failed because of mapping errors')
            stats['failed'] += 1
        else:
            success, created, errors = validate_and_save_company(company_data, LastUpdatedSource.worldbase)

            if success:
                if created:
                    stats['created'] += 1
                else:
                    stats['updated'] += 1
            else:
                logger.error(f'row {row_number} failed because of validation errors {errors}')
                stats['failed'] += 1

    return stats
