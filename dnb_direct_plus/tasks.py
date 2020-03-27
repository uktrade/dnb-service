import logging

from celery import shared_task
from django.utils import timezone

from company.models import Company
from dnb_direct_plus.monitoring import update_company_from_source


logger = logging.getLogger(__name__)


@shared_task
def update_company_from_api_data(api_data, enable_monitoring=False):
    """
    Create or update the company entry from DNB API data.
    if `enable_monitoring` is `True` then set `monitoring_status` to 'pending',
    if monitoring has not already been enabled for this company
    """

    duns_number = api_data["organization"]["duns"]

    logger.debug(f'Updating {duns_number}')

    try:
        company = Company.objects.get(duns_number=duns_number)
    except Company.DoesNotExist:
        company = Company()

    update_company_from_source(company, api_data, timezone.now(), enable_monitoring=enable_monitoring)
