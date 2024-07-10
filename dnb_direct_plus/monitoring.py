from contextlib import contextmanager
import copy
import csv
import datetime
import io
import json
import logging
import os
import zipfile

import pytz
from smart_open import open as smart_open

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db import transaction
from django.utils import timezone

from .client import api_request, DNBApiError
from company.constants import MonitoringStatusChoices
from company.models import Company, Country, IndustryCode, PrimaryIndustryCode, RegistrationNumber
from .mapping import extract_company_data


logger = logging.getLogger(__name__)


DNB_MONITORING_ADD_ENDPOINT = \
    '/v1/monitoring/registrations/{}/duns/add'.format(settings.DNB_MONITORING_REGISTRATION_REFERENCE)


@contextmanager
def open_zip_file(file_path, s3_client):
    """Open a zip archive and extract a file inside of the same name but with a .txt extension"""

    extracted_file_name = os.path.basename(file_path).replace('.zip', '.txt')

    with smart_open(
        file_path, 'rb', transport_params={'client': s3_client.s3_client}
    ) as file_:
        with zipfile.ZipFile(file_) as zip_archive:
            with zip_archive.open(extracted_file_name, 'r') as extracted_file:
                yield extracted_file


def _update_field(model_instance, field_name, value):
    """update a field on a model instance"""
    try:
        field_instance = model_instance._meta.get_field(field_name)
    except FieldDoesNotExist:
        return

    if value is None and not field_instance.null:
        value = ''

    setattr(model_instance, field_name, value)


def _parse_timestamp_from_file(file_name):
    """Parse the date from the filename, which is in the format: {RegistrationNumber_{timestamp}_[...].{ext}"}"""

    raw_time = os.path.basename(file_name.split('_')[1])

    timestamp = datetime.datetime.strptime(raw_time, '%Y%m%d%H%M%S')

    tz = pytz.timezone(settings.TIME_ZONE)
    return timestamp.replace(tzinfo=tz)


def _update_dict_key(source_data, elements, value):
    """Modify a nested key in a dict"""
    if len(elements) > 0:
        key = elements.pop(0)
        if key not in source_data:
            source_data[key] = {}
        source_data[key] = _update_dict_key(source_data[key], elements, value)
        return source_data
    else:
        return value


@transaction.atomic
def update_company_from_source(company, updated_source, updated_timestamp=None, enable_monitoring=False):
    """Rebuild a company entry, including related models with new api source data; NOTE: updated_source can be
    in the DNB direct plus CMPELK or companies list search api data type"""

    related_fields = {
        'registration_numbers': RegistrationNumber,
        'primary_industry_codes': PrimaryIndustryCode,
        'industry_codes': IndustryCode,
    }

    new_company_data = extract_company_data(updated_source)

    if updated_source.get('type', 'SEED') == 'UPDATE':
        if not company.source or new_company_data != extract_company_data(company.source):
            company.last_updated = timezone.now()

    # store fields in updated_source in the company instance
    for field, value in new_company_data.items():
        if field in ['address_country', 'registered_address_country']:
            country = Country.objects.get(iso_alpha2__iexact=value) if value else None
            setattr(company, field, country)
        elif field not in related_fields:
            _update_field(company, field, value)

    # "enable" monitoring if enable_monitoring=True.  NOTE: we only change the status if the current status is
    # not_enabled.  If it's already enabled, pending, or failed we do nothing.  Also, we don't actually
    # enable monitoring at this stage. Instead we set the status to "pending" and a cron task then adds
    # all companies with status= pending to the dnb monitoring registration via an api call
    if enable_monitoring and company.monitoring_status == MonitoringStatusChoices.not_enabled.name:
        company.monitoring_status = MonitoringStatusChoices.pending.name

    company.source = updated_source
    company.last_updated_source_timestamp = updated_timestamp
    company.save()

    # delete and recreate related models
    for field_name, model_class in related_fields.items():
        model_class.objects.filter(company=company).delete()
        for element in new_company_data[field_name]:
            instance = model_class()
            for field, value in element.items():
                _update_field(instance, field, value)
            instance.company = company
            instance.save()


def add_companies_to_monitoring_registration():
    """
    Take all entries from the Company model with status=pending and attempt to add them to the
    DNB monitoring registration.  On success all entries will have status of enabled - that is we assume
    that the registration was successful.

    If DNB fails to add the company to the monitoring registration the duns number will be listed in an
    exceptions file.  A scheduled job will process the exceptions file and set the monitoring status.
    """
    pending_registrations = Company.objects.filter(monitoring_status=MonitoringStatusChoices.pending.name)

    total = pending_registrations.count()

    logger.info(f"Attemping to register {total} companies for monitoring.")

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
            logger.info(
                f"Failed to register {total} companies for monitoring, these will be added to exceptions file."
            )
            raise DNBApiError(response_data)

    return total


def apply_update_to_company(update_data, timestamp):
    """Apply an individual update supplied from the DNB monitoring service to a company entry"""

    # all entries in NOTIFICATION files will have type = SEED or UPDATE.  SEEDFILE don't specify a type
    # but are always type = SEED
    update_type = update_data.get('type', 'SEED')

    if update_type not in ['SEED', 'UPDATE']:
        return False, f'skipping update type: {update_type}'

    duns_number = update_data['organization']['duns']

    try:
        company = Company.objects.get(duns_number=duns_number)
    except Company.DoesNotExist:
        # if type == SEED, we'll create a new company.  This has some use when initially populating the database
        # however, typically company entries will already exist as they are pre-created from API data
        company = Company(monitoring_status=MonitoringStatusChoices.enabled.name)

    if company.last_updated_source_timestamp and company.last_updated_source_timestamp > timestamp:
        return False, f'{duns_number}; update is older than last updated timestamp'

    # if type == "SEED" then update_data contains full copmany data, which overwrites company.source
    # if type == "UPDATE" then update_data contains a list of keys and changes, which we apply to the existing
    # company.source
    updated_source = copy.deepcopy(company.source) if update_type == 'UPDATE' else update_data

    if update_type == 'UPDATE':
        # type == UPDATE - a list of changed keys is supplied, which we apply to the original source
        # data, then rebuild the company models.  We can't proceed if there's a missing company.source
        if not company.id:
            return False, f'{duns_number}: update for company not in DB'
        if not company.source:
            return False, f'{duns_number}: No source data - cannot apply update'

        for update in update_data['elements']:
            _update_dict_key(updated_source, update['element'].split('.'), update['current'])

        updated_source['type'] = 'UPDATE'

    update_company_from_source(company, updated_source, timestamp)

    return True, ''


def process_exception_file(file_path, s3_client):
    """Process a DNB monitoring exceptions file and update Company.monitoring_status"""
    required_header = ['DUNS', 'Code', 'Information']

    file_name = os.path.basename(file_path)

    is_header = True

    total, total_success = 0, 0

    with open_zip_file(file_path, s3_client) as file_data:
        csv_data = csv.reader(io.TextIOWrapper(file_data), delimiter='\t')
        for line in csv_data:

            total += 1

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

                    logger.info(f'{file_name } Set monitoring_status for {duns_number} to failed')
                except Company.DoesNotExist:
                    logger.warning(f'{file_name}; {duns_number}; No company found with duns number')
                else:
                    total_success += 1

    return total, total_success


def process_notification_file(file_path, s3_client):
    """Process an update file"""

    timestamp = _parse_timestamp_from_file(file_path)

    file_name = os.path.basename(file_path)

    total, total_success = 0, 0

    with open_zip_file(file_path, s3_client) as file_data:
        for line_number, line in enumerate(file_data, 1):
            update_data = json.loads(line)

            total += 1

            if not isinstance(update_data, dict):
                logger.debug(f'{file_name}/{line_number} contains incomplete data: {update_data}')
                continue

            try:
                success, reason = apply_update_to_company(update_data, timestamp)
            except BaseException as exc:
                logger.error(f'{file_name}/{line_number} exception: {exc}; input data: {update_data}')
                continue

            if success:
                logger.info(f'{file_name}/{line_number}  Successfully processed')

                total_success += 1
            else:
                logger.warning(f'{file_name}/{line_number} failed reason: {reason}')

    return total, total_success
