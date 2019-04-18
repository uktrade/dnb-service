import pytest

from dnb_worldbase.constants import LEGAL_STATUS_CODE_MAPPING
from dnb_worldbase.mapping import (
    DataMappingError,
    dnb_country_lookup,
    extract_company_data,
    extract_registration_number,
    map_business_indicator,
    map_legal_status)

from company.constants import RegistrationNumberChoices


@pytest.mark.django_db
class TestDnbCountryLookup:
    @pytest.mark.parametrize('test_input,expected', [
        ('', None),
        ('790', 'GB'),
        ('805', 'US'),
    ])
    def test_valid_data(self, test_input, expected):
        assert dnb_country_lookup(test_input) == expected

    @pytest.mark.parametrize('test_input,exception,message', [
        ('99999', DataMappingError, '99999 is not in mapping'),
        # country does not have an associated ISO2 alpha code
        ('897', DataMappingError, '897 does not have an associated iso alpha 2 code'),
    ])
    def test_invalid_data(self, test_input, exception, message):
        with pytest.raises(exception) as ex:
            dnb_country_lookup(test_input)

        assert str(ex.value) == message


# def test_extract_employee_data(wb_data):
#     return {
#         'is_employees_number_estimated': False,
#         'employee_number': 5,
#     }
#
#
# def test_extract_sales_data(wb_data):
#     return {
#         'is_annual_sales_estimated': False,
#         'annual_sales': 8.00,
#     }


class TestMapBusinessIndicator:
    @pytest.mark.parametrize('test_input,expected', [
        ('Y', True),
        ('N', False),
    ])
    def test_valid_data(self, test_input, expected):
        assert map_business_indicator(test_input) == expected

    @pytest.mark.parametrize('test_input,exception,message', [
        ('', DataMappingError, 'no mapping for business indicator: '),
        ('X', DataMappingError, 'no mapping for business indicator: X'),
    ])
    def test_invalid_data(self, test_input, exception, message):
        with pytest.raises(exception) as ex:
            map_business_indicator(test_input)

        assert str(ex.value) == message


class TestMapLegalStatus:
    @pytest.mark.parametrize('test_input,expected', [
        (0, LEGAL_STATUS_CODE_MAPPING[0].name),
        (3, LEGAL_STATUS_CODE_MAPPING[3].name),
    ])
    def test_valid_data(self, test_input, expected):
        assert map_legal_status(test_input) == expected

    @pytest.mark.parametrize('test_input,exception,message', [
        ('9999', DataMappingError, 'no mapping for legal status code: 9999'),
        ('', DataMappingError, 'no mapping for legal status code: '),
    ])
    def test_invalid_data(self, test_input, exception, message):
        with pytest.raises(exception) as ex:
            map_legal_status(test_input)

        assert str(ex.value) == message


class TestExtractRegistrationNumber:
    @pytest.mark.parametrize('test_input,expected', [
        # No registration number provided for this company
        (
            {
                'National Identification System Code': '',
                'National Identification Number': '',
            },
            []
        ),
        # For the worldbase file 12 indicates a UK companies house number
        (
            {
                'National Identification System Code': '12',
                'National Identification Number': '1234567',
            },
            [
                {
                    'registration_type': RegistrationNumberChoices.uk_companies_house_number.name,
                    'registration_number': '1234567'
                }
            ]
        ),
    ])
    def test_valid_data(self, test_input, expected):
        assert extract_registration_number(test_input) == expected

    @pytest.mark.parametrize('test_input,exception,message', [
        # Invalid system code
        (
            {
                'National Identification System Code': '999',
                'National Identification Number': 'a number',
            },
            DataMappingError,
            'National ID code 999 is not in mapping',
        ),
    ])
    def test_invalid_data(self, test_input, exception, message):
        with pytest.raises(exception) as ex:
            extract_registration_number(test_input)

        assert str(ex.value) == message


@pytest.mark.django_db
class TestExtractCompanyData:
    @pytest.mark.parametrize('raw_data,expected', [
        ({
            'DUNS': '1234567',
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
            'Employees Total': 5,
            'Annual Sales Indicator': False,
            'Annual Sales in US dollars': 8.00,
        },
        {
            'duns_number': '1234567',
            'primary_name': 'Widgets Pty',
            'trading_names': ['Lots-a-widgets'],
            'registration_numbers': [
                {
                    'registration_type': 'uk_companies_house_number',
                    'registration_number': '1234567'
                }
            ],
            'address_line_1': 'address 1',
            'address_line_2': 'address 2',
            'address_town': 'city',
            'address_county': 'county',
            'address_postcode': 'postcode',
            'line_of_business': 'agriculture',
            'year_started': 2000,
            'global_ultimate_duns_number': '',
            'is_out_of_business': False,
            'legal_status': 'corporation',
            'is_employees_number_estimated': False,
            'employee_number': 5,
            'is_annual_sales_estimated': False,
            'annual_sales': 8.0,
            'address_country': 'GB'
        }),
    ])
    def test_valid_data(self, raw_data, expected):
        assert extract_company_data(raw_data) == expected
