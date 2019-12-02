import logging

from celery import shared_task
from django.utils import timezone

from dnb_direct_plus.monitoring import create_or_update_company


logger = logging.getLogger(__name__)


@shared_task
def update_company_and_enable_monitoring(api_data):
    logger.debug(f'Updating {api_data["duns"]}')
    create_or_update_company(api_data, timezone.now(), enable_monitoring=True)
