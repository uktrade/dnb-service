import codecs
import logging
from base64 import b64encode
from unittest import mock

import pytest
from django.test import override_settings
from freezegun import freeze_time
from notifications_python_client.errors import HTTPError

from company.constants import ChangeRequestStatus, InvestigationRequestStatus
from company.models import InvestigationRequest
from company.tasks import send_pending_change_requests, send_pending_investigation_requests
from company.tests.factories import ChangeRequestFactory
from company.utils import generate_investigation_request_csv
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
        mocked_send_email_notification.side_effect = mock.Mock(status_code=200)
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
            codecs.BOM_UTF8 + b"duns_number,changes\r\n000000005,Business Name: foo; Trading Name(s): ['foo ltd']\r\n000000006,"
            b'Business Name: bar\r\n'
        )
        expected_batch_1_encoded = b64encode(expected_batch_1).decode('ascii')
        expected_batch_2 = codecs.BOM_UTF8 + b'duns_number,changes\r\n000000007,Business Name: baz\r\n'
        expected_batch_2_encoded = b64encode(expected_batch_2).decode('ascii')

        mocked_send_email_notification.assert_has_calls(
            [
                mock.call(
                    email_address='foo@example.net',
                    template_id=TEMPLATE_IDS['change-request'],
                    personalisation={
                        'batch_identifier': 'Monday 25 November 2019',
                        'link_to_file': {'file': expected_batch_1_encoded, 'is_csv': True},
                    },
                ),
                mock.call(
                    email_address='foo@example.net',
                    template_id=TEMPLATE_IDS['change-request'],
                    personalisation={
                        'batch_identifier': 'Monday 25 November 2019 Part 2',
                        'link_to_file': {'file': expected_batch_2_encoded, 'is_csv': True},
                    },
                ),
            ],
        )

    @override_settings(CHANGE_REQUESTS_BATCH_SIZE=1)
    @override_settings(CHANGE_REQUESTS_RECIPIENTS=['foo@example.net'])
    @mock.patch('core.notify.notifications_client')
    def test_notify_error(self, mock_notify, caplog):
        """
        Test that when D&B service returns an error for a given batch, we log the error and process
        subsequent batches.
        """
        caplog.set_level(logging.INFO)
        with freeze_time('2019-11-25 12:00:01 UTC') as frozen_datetime:
            change_request_1 = ChangeRequestFactory(changes={'primary_name': 'foo'})
            # Ensure consistent ordering
            frozen_datetime.tick()
            change_request_2 = ChangeRequestFactory(changes={'primary_name': 'foo'})

            mock_notify.send_email_notification = mock.Mock()
            mock_notify.send_email_notification.side_effect = (
                HTTPError(response=mock.Mock(status_code=400)),
                {},
            )

            send_pending_change_requests.apply()

        assert caplog.messages[0] == 'Failed to process batch: Monday 25 November 2019'
        assert caplog.messages[1] == 'Successfully processed batch: Monday 25 November 2019 Part 2'

        change_request_1.refresh_from_db()
        change_request_2.refresh_from_db()

        assert change_request_1.status == 'pending'
        assert change_request_2.status == 'submitted'


class TestSendPendingInvestigationRequests:

    @pytest.fixture()
    def company_details(self):
        return {
            'primary_name': 'foo',
            'address_line_1': 'bar',
            'address_town': 'buz',
            'address_country': 'GB',
        }

    @mock.patch('company.tasks.send_investigation_request_batch')
    def test_empty(self, mock_send, company_details):
        """
        When there are no InvestigationRequest objects with status
        `pending`, nothing is sent.
        """
        InvestigationRequest(
            status=InvestigationRequestStatus.submitted.name,
            company_details=company_details,
        )

        send_pending_investigation_requests.apply()
        mock_send.assert_not_called()

    @freeze_time('2019-11-25 12:00:01 UTC')
    @mock.patch('company.tasks.send_investigation_request_batch')
    def test_single_batch(self, mock_send, company_details):
        """
        Test that the task works correctly for a single batch.
        """
        investigation_request = InvestigationRequest.objects.create(
            company_details=company_details,
        )

        send_pending_investigation_requests.apply()
        mock_send.assert_called_with(
            [investigation_request],
            'Monday 25 November 2019',
        )

    @freeze_time('2019-11-25 12:00:01 UTC')
    @override_settings(INVESTIGATION_REQUESTS_BATCH_SIZE=1)
    @mock.patch('company.tasks.send_investigation_request_batch')
    def test_multiple_batches(self, mock_send, company_details):
        """
        Test that the task works correctly for multiple batches.
        """
        investigation_requests = [
            InvestigationRequest.objects.create(company_details=company_details),
            InvestigationRequest.objects.create(company_details=company_details),
        ]

        send_pending_investigation_requests.apply()
        mock_send.call_count == 2
        mock_send.assert_called_with([investigation_requests[1]], 'Monday 25 November 2019 Part 2')

    @freeze_time('2019-11-25 12:00:01 UTC')
    @mock.patch('core.notify.notifications_client')
    @override_settings(INVESTIGATION_REQUESTS_RECIPIENTS=['foo@example.net'])
    def test_end_to_end(self, mock_notify, company_details, get_csv_bytes):
        """
        Integration test to ensure that the task calls through to the notify client
        correctly.
        """
        investigation_request = InvestigationRequest.objects.create(company_details=company_details)

        send_pending_investigation_requests.apply()
        csv_bytes = get_csv_bytes([investigation_request])

        assert mock_notify.send_email_notification.call_count == 1
        mock_notify.send_email_notification.assert_called_with(
            email_address='foo@example.net',
            template_id=TEMPLATE_IDS['investigation-request'],
            personalisation={
                'batch_identifier': 'Monday 25 November 2019',
                'link_to_file': {'file': b64encode(csv_bytes).decode('ascii'), 'is_csv': True},
            },
        )

    @override_settings(INVESTIGATION_REQUESTS_BATCH_SIZE=1)
    @override_settings(INVESTIGATION_REQUESTS_RECIPIENTS=['foo@example.net'])
    @mock.patch('core.notify.notifications_client')
    def test_notify_error(self, mock_notify, company_details, caplog):
        """
        Test that when D&B service returns an error for a given batch, we log the error and process
        subsequent batches.
        """
        caplog.set_level(logging.INFO)
        with freeze_time('2019-11-25 12:00:01 UTC') as frozen_datetime:
            investigation1 = InvestigationRequest.objects.create(company_details=company_details)
            # Ensure consistent ordering
            frozen_datetime.tick()
            investigation2 = InvestigationRequest.objects.create(company_details=company_details)

            mock_notify.send_email_notification = mock.Mock()
            mock_notify.send_email_notification.side_effect = (
                HTTPError(response=mock.Mock(status_code=400)),
                {},
            )

            send_pending_investigation_requests.apply()

        assert caplog.messages[0] == 'Failed to process batch: Monday 25 November 2019'
        assert caplog.messages[1] == 'Successfully processed batch: Monday 25 November 2019 Part 2'

        investigation1.refresh_from_db()
        investigation2.refresh_from_db()

        assert investigation1.status == 'pending'
        assert investigation2.status == 'submitted'
