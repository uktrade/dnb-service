import io
import csv

import pytest

from company.constants import LastUpdatedSource, LegalStatusChoices
from company.models import Company, Country

from ..ingest import validate_and_save_company, process_file
from ..constants import WB_HEADER_FIELDS

pytestmark = [
    pytest.mark.django_db
]


@pytest.fixture()
def test_input_data():
    """A set of fields required to validate the company form"""

    return {
        'duns_number': '123456789',
        'primary_name': 'widgets pty',
        'address_country': 'GB',
        'last_updated_source': LastUpdatedSource.api.name,
        'year_started': 1999,
        'legal_status': LegalStatusChoices.corporation.name,
        'registration_numbers': []
    }


def _lookup_country(value):
    if value:
        return Country.objects.get(iso_alpha2=value)
    else:
        return value


def _create_csv_row(data):
    """Takes a dict of column headings and values and returns an array of
    csv columns in the worldbase file format"""

    row = []

    for column in WB_HEADER_FIELDS:
        if column in data:
            row.append(data[column])
        else:
            row.append('')

    return row


def _build_test_csv(rows):
    """Builds a test worldbase file and returns a string buffer"""

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(WB_HEADER_FIELDS)

    for row in rows:
        writer.writerow(_create_csv_row(row))

    output.seek(0)

    return output


class TestValidateAndSaveCompany:
    def test_create_new_company(self, test_input_data):

        assert Company.objects.count() == 0

        success, created, errors = validate_and_save_company(test_input_data, LastUpdatedSource.api)

        assert (success, created, errors) == (True, True, None)

        assert Company.objects.count() == 1
        company = Company.objects.first()

        assert company.registrationnumber_set.count() == 0

        for field, value in test_input_data.items():

            expected = _lookup_country(value) if 'country' in field else value

            assert getattr(company, field) == expected

    def test_update_company(self, test_input_data):

        assert Company.objects.count() == 0

        Company.objects.create(
            duns_number='123456789',
            primary_name='test company',
            address_country=Country.objects.get(iso_alpha2='US'),
            last_updated_source=LastUpdatedSource.worldbase.name,
            year_started=2000,
            legal_status=LegalStatusChoices.partnership.name,
            is_out_of_business=True,
        )

        success, created, errors = validate_and_save_company(test_input_data, LastUpdatedSource.api)

        assert Company.objects.count() == 1
        assert (success, created, errors) == (True, False, None)

        company = Company.objects.first()

        for field, value in test_input_data.items():
            expected = _lookup_country(value) if 'country' in field else value
            assert getattr(company, field) == expected

    @pytest.mark.parametrize(
        'test_input,expected_errors',
        [
            (
                {
                    'duns_number': 'xxxxx',
                    'primary_name': 'widgets pty',
                    'address_country': 'GB',
                    'last_updated_source': LastUpdatedSource.api.name,
                    'year_started': 1999,
                    'legal_status': LegalStatusChoices.corporation.name,
                    'registration_numbers': [],
                },
                [{
                    'duns_number': ['Field should contain 9 numbers only']
                }],
            ),
            (
                {
                    'duns_number': '123345678',
                    'primary_name': 'widgets pty',
                    'address_country': 'GB',
                    'last_updated_source': LastUpdatedSource.api.name,
                    'year_started': 1999,
                    'legal_status': LegalStatusChoices.corporation.name,
                    'registration_numbers': [
                        {
                            'registration_type': 'invalid-type',
                            'registration_number': '12345',
                        }
                    ]
                },
                [{
                    'registration_type': ['Select a valid choice. invalid-type is not one of the available choices.']
                }],
            ),
        ],
    )
    def test_invalid_data(self, test_input, expected_errors):

        success, created, errors = validate_and_save_company(test_input, LastUpdatedSource.api)

        assert (success, created, errors) == (False, None, expected_errors)


class TestProcessFile:
    def _sample_data(self, extra_data={}):
        test_data = {
            'DUNS': '123456789',
            'Business Name': 'Widgets Pty',
            'Secondary Name': 'Lots-a-widgets',
            'National Identification System Code': '12',
            'National Identification Number': '1234567',
            'Street Address': 'address 1',
            'Street Address 2': 'address 2',
            'City Name': 'city',
            'State/Province Name': 'county',
            'Postal Code for Street Address': 'postcode',
            'Country Code': '000',
            'Line of Business': 'agriculture',
            'Year Started': '2000',
            'Global Ultimate DUNS Number': '',
            'Out of Business indicator': 'N',
            'Legal Status': '3',  # corporation
            'Employees Total Indicator': '2',
            'Employees Total': '5',
            'Annual Sales Indicator': False,
            'Annual Sales in US dollars': 8.00,
        }

        return dict(test_data, **extra_data)

    def test_create_success(self):
        csv_data = _build_test_csv([self._sample_data()])

        stats = process_file(csv_data)

        assert stats == {
            'failed': 0,
            'created': 1,
            'updated': 0,
        }

        assert Company.objects.count() == 1
        company = Company.objects.first()
        assert company.registrationnumber_set.count() == 1

    def test_update_success(self):
        csv_data = _build_test_csv([self._sample_data(), self._sample_data()])

        stats = process_file(csv_data)

        assert stats == {
            'failed': 0,
            'created': 1,
            'updated': 1,
        }

        assert Company.objects.count() == 1
        company = Company.objects.first()
        assert company.registrationnumber_set.count() == 1

    def test_bad_data(self):
        test_data = self._sample_data({
            'DUNS': 'invalid-duns-number'
        })

        csv_data = _build_test_csv([test_data])

        stats = process_file(csv_data)

        assert stats == {
            'failed': 1,
            'created': 0,
            'updated': 0,
        }

        assert Company.objects.count() == 0

    def test_mismatched_header_rows(self):
        csv_data = io.StringIO()

        bad_header_fields = WB_HEADER_FIELDS.copy()
        bad_header_fields[0] = 'not-expected'

        csv_data.write(','.join(bad_header_fields))

        csv_data.seek(0)

        with pytest.raises(AssertionError) as ex:
            process_file(csv_data)

        assert str(ex.value) == 'CSV column headings do not match expected values'

    def test_incorrect_column_length(self):
        csv_data = io.StringIO()

        bad_header_fields = WB_HEADER_FIELDS[:-5]

        csv_data.write(','.join(bad_header_fields))

        csv_data.seek(0)

        with pytest.raises(AssertionError) as ex:
            process_file(csv_data)
