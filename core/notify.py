import io

from django.conf import settings
from notifications_python_client import prepare_upload
from notifications_python_client.notifications import NotificationsAPIClient


notifications_client = NotificationsAPIClient(settings.GOVUK_NOTIFICATIONS_API_KEY)


TEMPLATE_IDS = {
    'change-request': 'd3fb8a4b-61d5-44f3-b9e9-8fa5a4894ffb',
}


def notify_by_email(email_address, template_identifier, context):
    """
    Notify an email address, using a GOVUK notify template and some template
    context.
    """
    # Go through the supplied context and ensure that any file objects are converted
    # to an uploadable string
    for key, value in context.items():
        if isinstance(value, io.IOBase):
            context[key] = prepare_upload(value)
    response = notifications_client.send_email_notification(
        email_address=email_address,
        template_id=template_identifier,
        personalisation=context,
    )
    return response
