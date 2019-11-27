from contextlib import contextmanager
import copy
import csv
import datetime
import io
import json
import logging
import os
import zipfile

from smart_open import open as smart_open

from django.conf import settings
from django.db import transaction

from .client import api_request, DNBApiError
from company.constants import MonitoringStatusChoices
from company.models import Company, Country, IndustryCode, PrimaryIndustryCode, RegistrationNumber
from .mapping import extract_company_data


logger = logging.getLogger(__name__)


DNB_MONITORING_ADD_ENDPOINT = \
    '/v1/monitoring/registrations/{}/duns/add'.format(settings.DNB_MONITORING_REGISTRATION_REFERENCE)


@contextmanager
def open_zip_file(file_path):
    """Open a zip archive and extract a file inside of the same name but with a .txt extension"""

    extracted_file_name = os.path.basename(file_path).replace('.zip', '.txt')

    with smart_open(file_path, 'rb') as file_:
        with zipfile.ZipFile(file_) as zip_archive:
            with zip_archive.open(extracted_file_name, 'r') as extracted_file:
                yield extracted_file


@transaction.atomic
def update_company_from_source(company, updated_source, updated_timestamp, enable_monitoring=False):

    related_fields = {
        'registration_numbers': RegistrationNumber,
        'primary_industry_codes': PrimaryIndustryCode,
        'industry_codes': IndustryCode,
    }

    allow_nulls = ['is_annual_sales_estimated', 'is_employees_number_estimated', 'year_started']

    new_company_data = extract_company_data(updated_source)

    if not company.source or new_company_data != extract_company_data(company.source):
        company.last_updated = datetime.datetime.now()

    for field, value in new_company_data.items():
        if field in ['address_country', 'registered_address_country']:
            country = Country.objects.get(iso_alpha2__iexact=value) if value else None
            setattr(company, field, country)
        elif field not in related_fields:
            if value is None and field not in allow_nulls:
                value = ''
            setattr(company, field, value)

    if enable_monitoring and company.monitoring_status == MonitoringStatusChoices.not_enabled.name:
        company.monitoring_status = MonitoringStatusChoices.pending.name

    company.source = updated_source
    company.last_updated_source_timestamp = updated_timestamp
    company.save()

    # update related models if they are modified
    for field_name, model_class in related_fields.items():
        model_class.objects.filter(company=company).delete()
        for element in new_company_data[field_name]:
            model_class.objects.create(company=company, **element)


def create_or_update_company(source_data, timestamp=None, enable_monitoring=False):
    """Create or update the company from api data """

    try:
        company = Company.objects.get(duns_number=source_data['duns_number'])
    except Company.DoesNotExist:
        company = Company()

    update_company_from_source(company, source_data, timestamp, enable_monitoring=enable_monitoring)


def add_companies_to_monitoring_registration():
    """
    Take all entries from the Company model with status=pending and attempt to add them to the
    DNB monitoring registration.  On success all entries will have status of enabled - that is we assume
    that the registration was successful.

    If DNB fails to add the company to the monitoring registration the duns number will be listed in an
    exceptions file.  A scheduled job will process the exceptions file and set the monitoring status to failed for
    companies listed in the file.
    """
    pending_registrations = Company.objects.filter(monitoring_status=MonitoringStatusChoices.pending.name)

    if pending_registrations.count() > 0:
        duns_list = '\n'.join(pending_registrations.values_list('duns_number', flat=True))

        files = {
            'duns': ('duns.txt', duns_list)
        }

        response = api_request('patch', DNB_MONITORING_ADD_ENDPOINT, files=files)

        if response.status_code == 202:
            pending_registrations.update(monitoring_status=MonitoringStatusChoices.enabled.name)

        else:
            response_data = response.json()
            raise DNBApiError(response_data)

        return pending_registrations.count()


def _parse_timestamp_from_file(file_name):
    """Parse the date from the filename, which is in the format: {RegistrationNumber_{timestamp}_[...].{ext}"}"""

    parts = os.path.basename(file_name.split('_'))

    return datetime.datetime.strptime(parts[1], '%Y%m%d%H%M%S')


def _update_dict_key(source_data, elements, value):
    """Modify a nested key in a dict"""
    if len(elements) > 0:
        key = elements.pop(0)
        source_data[key] = _update_dict_key(source_data[key], elements, value)
        return source_data
    else:
        return value


def apply_update_to_company(update_data, file_timestamp):
    """Apply an individual update supplied from the DNB monitoring service to a company entry"""

    duns_number = update_data['organization']['duns_number']

    try:
        company = Company.objects.get(duns_number=duns_number)
    except Company.DoesNotExist:
        return False, f'{duns_number}: update for company not in DB'

    if update_data['type'] != 'UPDATE':
        return False, f'{duns_number}: skipping {update_data["type"]} type'

    if not company.source:
        return False, f'{duns_number}: No source data'

    if company.last_updated_source_timestamp and company.last_updated_source_timestamp > file_timestamp:
        return False, f'{duns_number}; update is older than last updated timestamp'

    updated_source = copy.deepcopy(company.source)

    for update in update_data['elements']:
        try:
            _update_dict_key(updated_source, update['element'].split('.'), update['current'])
        except (KeyError, IndexError):
            logger.exception('Missing element')
            return False, f'Missing element: {update["element"]}'

    update_company_from_source(company, updated_source, file_timestamp)

    return True, ''


def process_seed_file(file_path):
    timestamp = _parse_timestamp_from_file(file_path)

    logger.info(f'Processing seed file: {file_path}')

    with open_zip_file(file_path) as file_data:
        for line_number, line in enumerate(file_data, 1):
            seed_data = json.loads(line)

            duns_number = seed_data['organization']['duns']

            try:
                company = Company.objects.get(duns_number=duns_number)
            except Company.DoesNotExist:
                logger.warning(
                    f'Seed data supplied for company not in DB: {duns_number}; '
                    f'line {line_number} of {file_path}; skipping')
                continue

            if company.last_updated_source_timestamp and timestamp < company.last_updated_source_timestamp:
                logger.info(f'Seed data for {duns_number} is older than last update; skipping')

            update_company_from_source(company, seed_data, )


def process_exception_file(file_path):
    """Process a DNB monitoring exceptions file and update Company.monitoring_status"""
    required_header = ['DUNS', 'Code', 'Information']

    is_header = True

    with open_zip_file(file_path) as file_data:
        csv_data = csv.reader(io.TextIOWrapper(file_data), delimiter='\t')
        for line in csv_data:

            if is_header:
                is_header = False
                if line != required_header:
                    raise ValueError(f'Expected header to be: {required_header} but got: {line} in {file_path}')
            else:
                duns_number = line[0]
                error_code  = line[1]
                description = line[2] if len(line) >= 3 else ''

                try:
                    company = Company.objects.get(duns_number=duns_number)
                    company.monitoring_status = MonitoringStatusChoices.failed.name
                    company.monitoring_status_detail = f'{error_code} {description}'
                    company.save()

                    logger.info(f'Set monitoring_status for {duns_number} to failed')
                except Company.DoesNotExist:
                    logger.warning(f'No company found with duns number: {duns_number}')


def process_update_file(file_path):
    """Process an update file"""
    timestamp = _parse_timestamp_from_file(file_path)

    logger.info(f'Processing update file: {file_path}')

    total, total_fail = 0, 0

    with open_zip_file(file_path) as file_data:
        for line_number, line in enumerate(file_data, 1):
            update_data = json.loads(line)

            success, reason = apply_update_to_company(update_data, timestamp)

            if not success:
                logger.warning(f'Error in {file_path} on {line_number} reason: {reason}')
                total_fail += 1

            total += 1

    return total, total_fail
