import io
from unittest import mock

from core.notify import notify_by_email


def test_notify_by_email_no_file(monkeypatch):
    """
    Test notify_by_email function when there is no file in the template context.
    """
    notifications_client_mock = mock.Mock()
    monkeypatch.setattr('core.notify.notifications_client', notifications_client_mock)
    email_address = 'joe.bloggs@example.net'
    template_id = 'foobar'
    context = {'foo': 'bar'}
    notify_by_email(email_address, template_id, context)
    notifications_client_mock.send_email_notification.assert_called_with(
        email_address=email_address,
        template_id=template_id,
        personalisation=context,
    )


def test_notify_by_email_with_file(monkeypatch):
    """
    Test notify_by_email function when there is a file in the template context.
    """
    notifications_client_mock = mock.Mock()
    monkeypatch.setattr('core.notify.notifications_client', notifications_client_mock)
    email_address = 'joe.bloggs@example.net'
    template_id = 'foobar'
    context = {
        'foo': 'bar',
        'file': io.BytesIO(b'foo bar baz'),
    }
    expected_personalisation = {
        **context,
        'file': {
            'confirm_email_before_download': None,
            'file': 'Zm9vIGJhciBiYXo=',
            'filename': None,
            'retention_period': None,
        },
    }
    notify_by_email(email_address, template_id, context)
    notifications_client_mock.send_email_notification.assert_called_with(
        email_address=email_address,
        template_id=template_id,
        personalisation=expected_personalisation,
    )
