import io

from django.conf import settings
from notifications_python_client import prepare_upload
from notifications_python_client.notifications import NotificationsAPIClient
from notifications_python_client.errors import HTTPError


notifications_client = NotificationsAPIClient(settings.GOVUK_NOTIFICATIONS_API_KEY)


TEMPLATE_IDS = {
    'change-request': '54d1cca9-5aea-4dcd-8d70-72c2fcc80f11',
    'investigation-request': 'd895cace-d746-4888-b08e-a8758ad7ba8b',
}


def notify_by_email(email_address, template_identifier, context, is_csv=False):
    """
    Notify an email address, using a GOVUK notify template and some template
    context.
    """
    # Go through the supplied context and ensure that any file objects are converted
    # to an uploadable string
    for key, value in context.items():
        if isinstance(value, io.IOBase):
            context[key] = prepare_upload(value, is_csv=is_csv)
    response = notifications_client.send_email_notification(
        email_address=email_address,
        template_id=template_identifier,
        personalisation=context,
    )
    if isinstance(response, HTTPError):
        response.raise_for_status()
    return response
