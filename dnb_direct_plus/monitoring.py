from contextlib import contextmanager
import csv
import datetime
import io
import logging
import os
import zipfile

from smart_open import open as smart_open

from django.conf import settings

from .client import api_request, DNBApiError
from company.constants import MonitoringStatusChoices
from company.models import Company
from company.serialisers import CompanySerialiser


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


def _compare_list(list1, list2):
    """Do the lists contain the same elements irrespective of order?"""

    if len(list1) != len(list2):
        return False

    for item in list1:
        if item not in list2:
            return False

    return True


def apply_dnb_monitoring_update(duns_number, diff_data):
    raise NotImplementedError


def create_or_update_company(api_data, updated_at=None, monitoring=False):
    """Create or update the company from api data
    """

    related_fields = {
        'registration_numbers': RegistrationNumber,
        'primary_industry_codes': IndustryCode,
        'industry_codes': PrimaryIndustryCode,
    }

    def _extract_company_fields(company_details):
        return {
            k: v for k, v in company_details if k not in related_fields
        }

    modified = False
    company_data = {}

    new_company_data = _extract_company_fields(api_data)

    company, created = Company.objects.get_or_create(duns_number=api_data['duns_number'], defaults=new_company_data)

    if not created:

        # if this update is older than the last applied update, then do nothing
        # if updated_at is not supplied it indicates that api_data is from a live api request, which means that
        # it's current. By contrast an update from monitoring data may resault in processing data is that hours old
        if updated_at and company.last_updated_source and company.last_updated_source > updated_at:
            logger.debug(f'not updating {company.duns_number} as update is older than last update')
            return False

        company_data = CompanySerialiser(company).data

        if _extract_company_fields(company_data) != new_company_data:
            for field, value in new_company_data.values():
                setattr(company, field, value)

    # updated related models if they are modified
    # TODO: implement transactions and locking
    for field_name, model_class in related_fields:
        if _compare_list(company_data.get(field_name, []), api_data[field_name]):
            model_class.objects.filter(company=company).delete()
            modified = True
            for item_data in api_data[field_name]:
                model_class.objects.create(company=company, **item_data)

    if modified:
        now = datetime.datetime.now()
        company.last_updated = now
        company.last_updated_source = updated_at if updated_at else now

    if monitoring and company.monitoring_status == MonitoringStatusChoices.not_enabled.name:
        company.monitoring_status = MonitoringStatusChoices.pending.name

    company.save()

    return modified


def add_companies_to_dnb_monitoring_registration():
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
    raise NotImplementedError
