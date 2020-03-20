from base64 import b64encode
from unittest import mock

import pytest
from django.test import override_settings
from freezegun import freeze_time

from company.constants import ChangeRequestStatus
from company.tasks import send_pending_change_requests
from company.tests.factories import ChangeRequestFactory
from core.notify import TEMPLATE_IDS


pytestmark = pytest.mark.django_db


class TestSendPendingChangeRequests:

    def test_no_pending_change_requests(self, monkeypatch):
        """
        Test that nothing is sent when there are no pending change requests.
        """
        mocked_send_change_request_batch = mock.Mock()
        monkeypatch.setattr('company.tasks.send_change_request_batch', mocked_send_change_request_batch)

        ChangeRequestFactory(status=ChangeRequestStatus.submitted.name, changes={'primary_name': 'foo'})

        send_pending_change_requests.apply()
        mocked_send_change_request_batch.assert_not_called()

    @freeze_time('2019-11-25 12:00:01 UTC')
    def test_single_batch(self, monkeypatch):
        """
        Test that the task works correctly for a single batch.
        """
        mocked_send_change_request_batch = mock.Mock()
        monkeypatch.setattr('company.tasks.send_change_request_batch', mocked_send_change_request_batch)

        change_request = ChangeRequestFactory(changes={'primary_name': 'foo'})

        send_pending_change_requests.apply()
        mocked_send_change_request_batch.assert_called_with([change_request], 'Monday 25 November 2019')

    @freeze_time('2019-11-25 12:00:01 UTC', tick=True)
    @override_settings(CHANGE_REQUESTS_BATCH_SIZE=2)
    def test_multiple_batches(self, monkeypatch):
        """
        Test that the task works correctly for multiple batches.
        """
        mocked_send_change_request_batch = mock.Mock()
        monkeypatch.setattr('company.tasks.send_change_request_batch', mocked_send_change_request_batch)

        change_requests = [
            ChangeRequestFactory(changes={'primary_name': 'foo'}),
            ChangeRequestFactory(changes={'primary_name': 'bar'}),
            ChangeRequestFactory(changes={'primary_name': 'baz'}),
        ]

        send_pending_change_requests.apply()
        mocked_send_change_request_batch.assert_has_calls(
            [
                mock.call([change_requests[0], change_requests[1]], 'Monday 25 November 2019'),
                mock.call([change_requests[2]], 'Monday 25 November 2019 Part 2'),
            ],
        )

    @freeze_time('2019-11-25 12:00:01 UTC', tick=True)
    @override_settings(CHANGE_REQUESTS_BATCH_SIZE=2, CHANGE_REQUESTS_RECIPIENTS=['foo@example.net'])
    def test_multiple_batches_calls_through_to_notify(self, monkeypatch):
        """
        Integration test to ensure that the task calls through to the notify client correctly for multiple batches.
        """
        mocked_notifications_client = mock.Mock()
        mocked_send_email_notification = mocked_notifications_client.send_email_notification
        monkeypatch.setattr('core.notify.notifications_client', mocked_notifications_client)

        ChangeRequestFactory(
            duns_number='000000005', changes={'primary_name': 'foo', 'trading_names': ['foo ltd']}
        )
        ChangeRequestFactory(duns_number='000000006', changes={'primary_name': 'bar'})
        ChangeRequestFactory(duns_number='000000007', changes={'primary_name': 'baz'})

        send_pending_change_requests.apply()

        # Simulate the effect of notifications_python_client.utils.prepare_upload to set expected file content
        # See: https://github.com/alphagov/notifications-python-client/blob/master/notifications_python_client/utils.py
        expected_batch_1 = (
            b"duns_number,changes\r\n000000005,Business Name: foo; Trading Name(s): ['foo ltd']\r\n000000006,"
            b'Business Name: bar\r\n'
        )
        expected_batch_1_encoded = b64encode(expected_batch_1).decode('ascii')
        expected_batch_2 = b'duns_number,changes\r\n000000007,Business Name: baz\r\n'
        expected_batch_2_encoded = b64encode(expected_batch_2).decode('ascii')

        mocked_send_email_notification.assert_has_calls(
            [
                mock.call(
                    email_address='foo@example.net',
                    template_id=TEMPLATE_IDS['change-request'],
                    personalisation={
                        'batch_identifier': 'Monday 25 November 2019',
                        'link_to_file': {'file': expected_batch_1_encoded},
                    },
                ),
                mock.call(
                    email_address='foo@example.net',
                    template_id=TEMPLATE_IDS['change-request'],
                    personalisation={
                        'batch_identifier': 'Monday 25 November 2019 Part 2',
                        'link_to_file': {'file': expected_batch_2_encoded},
                    },
                ),
            ],
        )
