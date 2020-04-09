import io
import csv
from unittest import mock

import pytest
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time
from notifications_python_client.errors import HTTPError

from company.models import InvestigationRequest
from company.utils import (
    generate_change_request_csv,
    generate_investigation_request_csv,
    send_change_request_batch,
    send_investigation_request_batch,
)
from company.tests.factories import ChangeRequestFactory
from company.constants import ChangeRequestStatus, InvestigationRequestStatus
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


class TestGenerateInvestigationRequestCSV:

    def test_index_error(self):
        """
        Given an empty list of InvestigationRequest objects, the function
        should throw an IndexError.
        """
        with pytest.raises(IndexError):
            generate_investigation_request_csv([])

    @pytest.mark.parametrize(
        'company_details, expected_output',
        (
            (
                {
                    'primary_name': 'Foo',
                    'domain': 'foo.com',
                    'telephone_number': '(+44) 123 45678',
                    'address_line_1': 'Bar',
                    'address_line_2': 'Buz',
                    'address_town': 'London',
                    'address_county': 'London',
                    'address_country': 'GB',
                    'address_postcode': 'ABC DEF',
                },
                (
                    (
                        'ID',
                        'Name',
                        'Address',
                        'Domain',
                        'Telephone Number',
                        'DUNS Number',
                    ),
                    (
                        mock.ANY,
                        'Foo',
                        'Bar, Buz, London, London, ABC DEF, GB',
                        'foo.com',
                        '(+44) 123 45678',
                        '',
                    ),
                ),
            ),
        ),
    )
    def test_csv(self, company_details, expected_output):
        """
        Given a valid record, the function will return a CSV in a valid format.
        """
        investigation_request = InvestigationRequest(company_details=company_details)
        content = generate_investigation_request_csv([investigation_request])
        reader = csv.reader(content, dialect='excel', delimiter=',')
        [row for row in reader] == expected_output


class TestSendInvestigationRequestBatch:

    @freeze_time('2019-11-25 12:00:01 UTC')
    @override_settings(
        INVESTIGATION_REQUESTS_RECIPIENTS=[
            'foo@example.net',
            'bar@example.net',
        ]
    )
    @mock.patch('company.utils.notify_by_email')
    def test_success(self, mock_notify, get_csv_bytes):
        """
        Given a list of `InvestigationRequest` objects and a `batch_identifier`:

        1) The function will trigger a valid call to `notify_by_email`
        2) The `InvestigationRequest` objects will be marked as `submitted`.
        """
        investigation_request = InvestigationRequest(
            company_details={
                'primary_name': 'Foo',
                'domain': 'foo.com',
                'telephone_number': '(+44) 123 45678',
                'address_line_1': 'Bar',
                'address_line_2': 'Buz',
                'address_town': 'London',
                'address_county': 'London',
                'address_country': 'GB',
                'address_postcode': 'ABC DEF',
            },
        )

        send_investigation_request_batch(
            [investigation_request],
            'Batch 1',
        )
        csv_bytes = get_csv_bytes([investigation_request])

        mock_notify.assert_called_with(
            'bar@example.net',
            TEMPLATE_IDS['investigation-request'],
            {
                'batch_identifier': 'Batch 1',
                'link_to_file': mock.ANY,
            }
        )
        assert mock_notify.call_count == 2
        assert mock_notify.call_args[0][2]['link_to_file'].getvalue() == csv_bytes

        assert investigation_request.status == InvestigationRequestStatus.submitted.name
        assert investigation_request.submitted_on == timezone.now()

    @freeze_time('2019-11-25 12:00:01 UTC')
    @override_settings(
        INVESTIGATION_REQUESTS_RECIPIENTS=[
            'foo@example.net',
            'bar@example.net',
        ]
    )
    @mock.patch('company.utils.notify_by_email')
    def test_failure(self, mock_notify):
        """
        Test that send_change_request_batch fails gracefully without marking
        InvestigationRequests as submitted.
        """
        mock_notify.side_effect = HTTPError()
        investigation_request = InvestigationRequest(
            company_details={
                'primary_name': 'Foo',
                'domain': 'foo.com',
                'telephone_number': '(+44) 123 45678',
                'address_line_1': 'Bar',
                'address_line_2': 'Buz',
                'address_town': 'London',
                'address_county': 'London',
                'address_country': 'GB',
                'address_postcode': 'ABC DEF',
            },
        )

        with pytest.raises(HTTPError):
            send_investigation_request_batch(
                [investigation_request],
                'Batch 1',
            )

        assert investigation_request.status == InvestigationRequestStatus.pending.name
        assert investigation_request.submitted_on == None
