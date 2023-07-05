import csv
import io
from collections import OrderedDict

import pytest
from django.utils import timezone
from freezegun import freeze_time

from company.constants import LegalStatusChoices
from company.models import Company, Country
from company.serialisers import CompanySerialiser

from ..constants import WB_HEADER_FIELDS
from ..ingest import process_file, update_company

pytestmark = [
    pytest.mark.django_db
]


@pytest.fixture()
def test_input_data():
    """A set of fields required to validate the company form"""

    return {
        'DUNS Number': '123456789',
        'Business Name': 'Widgets Pty',
        'Secondary Name': 'Lots-a-widgets',
        'National Identification System Code': '12',
        'National Identification Number': '1234567',
        'Street Address': 'address 1',
        'Street Address 2': 'address 2',
        'City Name': 'city',
        'State/Province Name': 'county',
        'State/Province Abbreviation': '',
        'Postal Code for Street Address': 'postcode',
        'Country Code': '790',
        'Line of Business': 'agriculture',
        'Year Started': '2000',
        'Global Ultimate DUNS Number': '',
        'Out of Business indicator': 'N',
        'Legal Status': '3',  # corporation
        'Employees Total Indicator': '2',
        'Employees Total': 5,
        'Annual Sales Indicator': '2',
        'Annual Sales in US dollars': 8.00,
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


class TestUpdateCompany:
    @freeze_time('2019-11-25 12:00:01 UTC')
    def test_source_and_updated_field(self, test_input_data):

        update_company(test_input_data)

        assert Company.objects.count() == 1
        company = Company.objects.first()

        assert company.worldbase_source == test_input_data
        assert company.worldbase_source_updated_timestamp == timezone.now()

    def test_create_new_company(self, test_input_data):
        assert Company.objects.count() == 0

        created = update_company(test_input_data)

        assert created

        assert Company.objects.count() == 1
        company = Company.objects.first()

        assert company.registration_numbers.count() == 1

        serialiser = CompanySerialiser(company)

        assert serialiser.data == {
            'last_updated': None,
            'duns_number': '123456789',
            'parent_duns_number': None,
            'global_ultimate_duns_number': '',
            'primary_name': 'Widgets Pty',
            'global_ultimate_primary_name': '',
            'trading_names': ['Lots-a-widgets'],
            'domain': '',
            'address_line_1': 'address 1',
            'address_line_2': 'address 2',
            'address_town': 'city',
            'address_county': 'county',
            'address_area_name': '',
            'address_area_abbrev_name': '',
            'address_country': 'GB',
            'address_postcode': 'postcode',
            'registered_address_line_1': '',
            'registered_address_line_2': '',
            'registered_address_town': '',
            'registered_address_county': '',
            'registered_address_area_name': '',
            'registered_address_area_abbrev_name': '',
            'registered_address_country': None,
            'registered_address_postcode': '',
            'line_of_business': 'agriculture',
            'is_out_of_business': False,
            'year_started': 2000,
            'employee_number': 5,
            'is_employees_number_estimated': None,
            'annual_sales': 8.0,
            'annual_sales_currency': '',
            'is_annual_sales_estimated': True,
            'legal_status': 'corporation',
            'registration_numbers': [
                OrderedDict([('registration_type', 'uk_companies_house_number'),
                             ('registration_number', '1234567')])],
            'primary_industry_codes': [],
            'industry_codes': []
        }

    def test_update_company(self, test_input_data):
        assert Company.objects.count() == 0

        Company.objects.create(
            duns_number='123456789',
            primary_name='test company',
            address_country=Country.objects.get(iso_alpha2='US'),
            year_started=2000,
            legal_status=LegalStatusChoices.partnership.name,
            is_out_of_business=True,
            source=None,
            last_updated=None,
        )

        created = update_company(test_input_data)

        assert not created
        assert Company.objects.count() == 1

        company = Company.objects.first()

        serialiser = CompanySerialiser(company)

        assert serialiser.data == {
            'last_updated': None,
            'duns_number': '123456789',
            'parent_duns_number': None,
            'global_ultimate_duns_number': '',
            'primary_name': 'Widgets Pty',
            'global_ultimate_primary_name': '',
            'trading_names': ['Lots-a-widgets'],
            'domain': '',
            'address_line_1': 'address 1',
            'address_line_2': 'address 2',
            'address_town': 'city',
            'address_county': 'county',
            'address_area_name': '',
            'address_area_abbrev_name': '',
            'address_country': 'GB',
            'address_postcode': 'postcode',
            'registered_address_line_1': '',
            'registered_address_line_2': '',
            'registered_address_town': '',
            'registered_address_county': '',
            'registered_address_area_name': '',
            'registered_address_area_abbrev_name': '',
            'registered_address_country': None,
            'registered_address_postcode': '',
            'line_of_business': 'agriculture',
            'is_out_of_business': False,
            'year_started': 2000,
            'employee_number': 5,
            'is_employees_number_estimated': None,
            'annual_sales': 8.0,
            'annual_sales_currency': '',
            'is_annual_sales_estimated': True,
            'legal_status': 'corporation',
            'registration_numbers': [
                OrderedDict([('registration_type', 'uk_companies_house_number'),
                             ('registration_number', '1234567')])],
            'primary_industry_codes': [],
            'industry_codes': []
        }

    def test_update_company_with_api_data(self, test_input_data):
        assert Company.objects.count() == 0

        original_company = Company.objects.create(
            duns_number='123456789',
            primary_name='test company',
            address_country=Country.objects.get(iso_alpha2='US'),
            year_started=2000,
            legal_status=LegalStatusChoices.partnership.name,
            is_out_of_business=True,
            source='{"some_data": "do not amend"}',
        )

        original_company_data = CompanySerialiser(original_company)

        created = update_company(test_input_data)

        assert not created
        assert Company.objects.count() == 1

        company = Company.objects.first()

        serialiser = CompanySerialiser(company)

        assert serialiser.data == original_company_data.data

    @pytest.mark.parametrize(
        'test_input,exception,message',
        [
            (
                {
                    'DUNS': 'xxxxx',
                    'Business Name': 'widgets pty',
                    'Country Code': 'GB',
                    'Year Started': 1999,
                    'Secondary Name': 'widgets limited',
                    'Legal Status': LegalStatusChoices.corporation.name,
                    'National Identification System Code': '12',
                    'National Identification Number': '1234567',
                },
                KeyError,
                'Secondary Name',
            ),
        ],
    )
    def test_invalid_data(self, test_input, exception, message):
        with pytest.raises(exception) as ex:
            update_company(test_input)

            assert ex.value == message


class TestProcessFile:
    def _sample_data(self, extra_data={}):
        test_data = {
            'DUNS Number': '123456789',
            'Business Name': 'Widgets Pty',
            'Secondary Name': 'Lots-a-widgets',
            'National Identification System Code': '12',
            'National Identification Number': '1234567',
            'Street Address': 'address 1',
            'Street Address 2': 'address 2',
            'City Name': 'city',
            'State/Province Name': 'county',
            'State/Province Abbreviation': '',
            'Postal Code for Street Address': 'postcode',
            'Country Code': '790',
            'Line of Business': 'agriculture',
            'Year Started': '2000',
            'Global Ultimate DUNS Number': '',
            'Out of Business indicator': 'N',
            'Legal Status': '3',  # corporation
            'Employees Total Indicator': '2',
            'Employees Total': '5',
            'Annual Sales Indicator': '2',
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
        assert company.registration_numbers.count() == 1

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
        assert company.registration_numbers.count() == 1

    def test_bad_data(self):
        test_data = self._sample_data({
            'DUNS Number': 'invalid-duns-number'
        })

        csv_data = _build_test_csv([test_data])

        stats = process_file(csv_data)

        assert stats == {
            'failed': 1,
            'created': 0,
            'updated': 0,
        }

        assert Company.objects.count() == 0
