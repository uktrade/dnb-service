import logging

from celery import shared_task
from django.conf import settings
from django.utils.timezone import now
from notifications_python_client.errors import HTTPError

from company.constants import ChangeRequestStatus, InvestigationRequestStatus
from company.models import ChangeRequest, InvestigationRequest
from company.utils import (
    send_change_request_batch,
    send_investigation_request_batch,
)


logger = logging.getLogger(__name__)


def get_batches(iterable, n):
    """
    Yield successive n-sized batches from iterable.
    """
    batch_identifier_base = now().strftime('%A %d %B %Y')
    for batch_number, i in enumerate(range(0, len(iterable), n), 1):
        batch_identifier = batch_identifier_base
        if batch_number > 1:
            batch_identifier = f'{batch_identifier_base} Part {batch_number}'
        yield (iterable[i:i + n], batch_identifier)


@shared_task
def send_pending_change_requests():
    """
    Send all pending ChangeRequests through to D&B as a CSV file attached to an email notification.
    """
    # Grabbing all of the pending change requests at once as a list assumes that this will be a managable amount of
    # change requests. We are expecting ~50 change requests per-day maximum
    pending_change_requests = list(
        ChangeRequest.objects.filter(status=ChangeRequestStatus.pending.name).order_by('created_on')
    )

    batches = get_batches(pending_change_requests, settings.CHANGE_REQUESTS_BATCH_SIZE)
    for batch, batch_identifier in batches:
        try:
            send_change_request_batch(batch, batch_identifier)
            logger.info(f'Successfully processed batch: {batch_identifier}')
        except HTTPError:
            logger.exception(f'Failed to process batch: {batch_identifier}')


@shared_task
def send_pending_investigation_requests():
    """
    Send all pending InvestigationRequests to D&B in a CSV file
    attached to an email.
    """
    pending_investigation_requests = list(
        InvestigationRequest.objects.filter(
            status=InvestigationRequestStatus.pending.name
        ).order_by('created_on')
    )

    batches = get_batches(
        pending_investigation_requests,
        settings.INVESTIGATION_REQUESTS_BATCH_SIZE
    )

    for batch, batch_identifier in batches:
        try:
            send_investigation_request_batch(batch, batch_identifier)
            logger.info(f'Successfully processed batch: {batch_identifier}')
        except HTTPError:
            logger.exception(f'Failed to process batch: {batch_identifier}')
