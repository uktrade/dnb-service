import io
import csv

import pytest

from company.utils import generate_change_request_csv
from company.tests.factories import ChangeRequestFactory


@pytest.mark.django_db
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
        csv_file_contents = csv_file.read().decode('utf-8')
        csv_file_stringio = io.StringIO(csv_file_contents)
        reader = csv.reader(csv_file_stringio, dialect='excel', delimiter=',')
        for row, expected_row in zip(reader, expected_rows):
            assert row == expected_row

    def test_exception_raised_for_empty_change_requests(self):
        """
        Test that an IndexError is raised when generate_change_request_csv is called with an empty list.
        """
        with pytest.raises(IndexError):
            generate_change_request_csv([])
