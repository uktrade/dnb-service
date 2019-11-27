from contextlib import contextmanager
import csv
import io
import logging
import os
import zipfile

from smart_open import open as smart_open

from django.conf import settings

from .client import api_request, DNBApiError
from company.models import Company
from company.constants import MonitoringStatusChoices



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


def add_companies_to_dnb_monitoring_registration():
    """
    Take all entries from the Company model with status=pending and attempt to add them to the
    DNB monitoring registration.  On success all entries will have status of Submitted.  If the api call is successful
    it is assumed that the company was successfully added to the registration.  If there is a failure, we receive
    notification from DNB later on.
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
