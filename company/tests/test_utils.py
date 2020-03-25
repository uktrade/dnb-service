import io
import csv
from unittest import mock

import pytest
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time
from notifications_python_client.errors import HTTPError

from company.utils import generate_change_request_csv, send_change_request_batch
from company.tests.factories import ChangeRequestFactory
from company.constants import ChangeRequestStatus
from core.notify import TEMPLATE_IDS


pytestmark = pytest.mark.django_db


class TestGenerateChangeRequestCSV:

    def test_csv_generated_correctly(self):
        """
        Test that the csv is generated as expected for both a partial and a full change request.
        """
        partial_change_request = ChangeRequestFactory(changes={'primary_name': 'Foo'})
        full_change_request = ChangeRequestFactory(changes={
            'primary_name': 'Bar',
            'trading_names': ['Bar inc', 'Bar LTD'],
            'domain': 'example.net',
            'address_line_1': '123 Fake Lane',
            'address_line_2': 'Somewhere',
            'address_town': 'Southampton',
            'address_county': 'Hampshire',
            'address_postcode': 'SO31 9TB',
            'address_country': 'GB',
            'registered_address_line_1': '123 Fake Street',
            'registered_address_line_2': 'Some Place',
            'registered_address_town': 'London',
            'registered_address_county': 'Greater London',
            'registered_address_postcode': 'W1 9TB',
            'registered_address_country': 'GB',
            'employee_number': 190,
            'annual_sales': 1050.0,
            'annual_sales_currency': 'GBP',
        })
        expected_rows = [
            ['duns_number', 'changes'],
            [partial_change_request.duns_number, 'Business Name: Foo'],
            [
                full_change_request.duns_number,
                (
                    'Business Name: Bar; '
                    "Trading Name(s): ['Bar inc', 'Bar LTD']; "
                    'Website Domain: example.net; '
                    'Address: 123 Fake Lane, Somewhere, Southampton, Hampshire, SO31 9TB, GB; '
                    'Registered Address: 123 Fake Street, Some Place, London, Greater London, W1 9TB, GB; '
                    'Employee Number: 190; '
                    'Annual Sales: 1050.0; '
                    'Annual Sales Currency: GBP'
                ),
            ],
        ]
        csv_file = generate_change_request_csv([partial_change_request, full_change_request])
        # Convert the byte file object in to a string
        csv_file_contents = csv_file.read().decode('utf-8')
        # Put the string CSV content in to a StringIO object so that we can use the csv module to read it
        csv_file_stringio = io.StringIO(csv_file_contents)
        reader = csv.reader(csv_file_stringio, dialect='excel', delimiter=',')
        for expected_row, row in zip(expected_rows, reader):
            assert row == expected_row

    def test_exception_raised_for_empty_change_requests(self):
        """
        Test that an IndexError is raised when generate_change_request_csv is called with an empty list.
        """
        with pytest.raises(IndexError):
            generate_change_request_csv([])


class TestSendChangeRequestBatch:

    @freeze_time('2019-11-25 12:00:01 UTC')
    @override_settings(CHANGE_REQUESTS_RECIPIENTS=['foo@example.net', 'bar@example.net'])
    def test_batch_sends_successfully(self, monkeypatch):
        """
        Test that send_change_request_batch triggers a notify_by_email call and that
        change requests are marked as submitted.
        """
        mocked_notify_by_email = mock.Mock()
        monkeypatch.setattr('company.utils.notify_by_email', mocked_notify_by_email)
        mocked_generate_change_request_csv = mock.Mock()
        monkeypatch.setattr('company.utils.generate_change_request_csv', mocked_generate_change_request_csv)
        change_requests = [
            ChangeRequestFactory(changes={'primary_name': 'foo'}),
            ChangeRequestFactory(changes={'trading_names': ['bar']}),
        ]
        batch_identifier = 'Batch 1'
        send_change_request_batch(change_requests, batch_identifier)
        mocked_notify_by_email.assert_has_calls(
            [
                mock.call(
                    'foo@example.net',
                    TEMPLATE_IDS['change-request'],
                    {
                        'batch_identifier': 'Batch 1',
                        'link_to_file': mocked_generate_change_request_csv.return_value,
                    }
                ),
                mock.call(
                    'bar@example.net',
                    TEMPLATE_IDS['change-request'],
                    {
                        'batch_identifier': 'Batch 1',
                        'link_to_file': mocked_generate_change_request_csv.return_value,
                    }
                ),
            ]
        )
        # Ensure that change request records are now set to submitted
        for change_request in change_requests:
            change_request.refresh_from_db()
            assert change_request.status == ChangeRequestStatus.submitted.name
            assert change_request.submitted_on == timezone.now()

    @override_settings(CHANGE_REQUESTS_RECIPIENTS=['foo@example.net', 'bar@example.net'])
    def test_send_fails_ensure_change_requests_pending(self, monkeypatch):
        """
        Test that send_change_request_batch fails gracefully without marking
        change requests as submitted.
        """
        mocked_notify_by_email = mock.Mock()
        mocked_notify_by_email.side_effect = HTTPError()
        monkeypatch.setattr('company.utils.notify_by_email', mocked_notify_by_email)
        change_requests = [
            ChangeRequestFactory(changes={'primary_name': 'foo'}),
            ChangeRequestFactory(changes={'trading_names': ['bar']}),
        ]
        batch_identifier = 'Batch 1'
        with pytest.raises(HTTPError):
            send_change_request_batch(change_requests, batch_identifier)
        # Ensure that change request records are not set to submitted
        for change_request in change_requests:
            change_request.refresh_from_db()
            assert change_request.status == ChangeRequestStatus.pending.name
            assert change_request.submitted_on is None
