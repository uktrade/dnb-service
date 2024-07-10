import logging
import os

from celery import shared_task

from django.conf import settings
from django.utils import timezone

from company.models import Company
from dnb_direct_plus.models import MonitoringFileRecord
from dnb_direct_plus.monitoring import process_exception_file, process_notification_file
from dnb_direct_plus.monitoring import (
    add_companies_to_monitoring_registration,
    update_company_from_source,
)
from dnb_direct_plus.s3_client import S3Client

logger = logging.getLogger(__name__)


@shared_task
def update_company_and_enable_monitoring(api_data):
    """Create or update the company entry and set monitoring_status to 'pending' if not already enabled"""

    duns_number = api_data["organization"]["duns"]

    logger.debug(f'Updating {duns_number}')

    try:
        company = Company.objects.get(duns_number=duns_number)
    except Company.DoesNotExist:
        company = Company()

    update_company_from_source(company, api_data, timezone.now(), enable_monitoring=True)


@shared_task
def register_companies_for_dnb_api_monitoring():
    """
    Registers companies to be monitored by the external D&B API.

    If the registration fails, the company is listed in an exceptions file by the external
    D&B API and processed by process_updates_from_dnb_api_monitoring_data task later.
    """
    logger.info("Starting task register_companies_for_dnb_api_monitoring.")

    total = add_companies_to_monitoring_registration()

    logger.info(f"{total} companies added to monitoring registration")


@shared_task
def process_updates_from_dnb_api_monitoring_data():
    """
    Processes any updates for companies that are registered with the external
    D&B API.

    AND

    Processes exception files for any companies which failed to be registered
    to the external D&B API.
    """
    logger.info("Checking for company updates or exceptions received from D&B.")

    s3_client = S3Client()
    files = s3_client.list_files(settings.DNB_MONITORING_S3_BUCKET)

    summary = []

    for file_name in files:

        if not file_name.startswith(settings.DNB_MONITORING_REGISTRATION_REFERENCE):
            # file does not relate to the monitoring registration
            continue

        if "HEADER" in file_name:
            continue

        if file_name.startswith(settings.DNB_ARCHIVE_PATH):
            continue

        if MonitoringFileRecord.objects.filter(file_name=file_name).exists():
            logger.info(f"{file_name} already processed; skipping")
            continue

        if "Exceptions" in file_name:
            handler = process_exception_file
        elif "NOTIFICATION" in file_name or "SEEDFILE" in file_name:
            handler = process_notification_file
        else:
            continue

        bucket_path = os.path.join(
            "s3://", settings.DNB_MONITORING_S3_BUCKET, file_name
        )

        logger.info(f"Processing: {file_name}")

        total, total_success = handler(bucket_path, s3_client)

        summary.append(dict(file=file_name, total=total, failed=total - total_success))
        MonitoringFileRecord.objects.create(
            file_name=file_name, total=total, failed=total - total_success
        )

        if settings.DNB_ARCHIVE_PROCESSED_FILES:
            s3_client.archive_file(file_name)

    summary_text = "\n".join(
        "{file}\t\tTotal: {total}\tFailed: {failed}".format(**line) for line in summary
    )

    # The sum of all the companies successfully updated.
    total_successful_updates = sum(line["total"] - line["failed"] for line in summary)
    logger.info(f"A total of {total_successful_updates} companies were updated.")

    if summary_text:
        logger.info(summary_text)
