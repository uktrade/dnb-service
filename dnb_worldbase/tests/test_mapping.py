import pytest

from company.constants import LegalStatusChoices, RegistrationNumberChoices
from dnb_worldbase.constants import LEGAL_STATUS_CODE_MAPPING
from dnb_worldbase.mapping import (
    DataMappingError,
    dnb_country_lookup,
    EmployeesIndicator,
    extract_business_indicator,
    extract_company_data,
    extract_employees,
    extract_legal_status,
    extract_registration_number,
    extract_turnover,
    TurnoverIndicator)


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


class TestExtractEmployees:
    """Tests for the _extract_employees function."""

    @pytest.mark.parametrize(
        'wb_record,expected_output',
        (
            # (estimated) Employees Total used
            (
                {
                    'Employees Total': '1',
                    'Employees Total Indicator': EmployeesIndicator.ESTIMATED,
                },
                (1, True),
            ),

            # (estimated because 'modelled') Employees Total used
            (
                {
                    'Employees Total': '1',
                    'Employees Total Indicator': EmployeesIndicator.MODELLED,
                },
                (1, True),
            ),

            # (estimated because 'low end of range') Employees Total used
            (
                {
                    'Employees Total': '1',
                    'Employees Total Indicator': EmployeesIndicator.LOW_END_OF_RANGE,
                },
                (1, True),
            ),

            # (actual) Employees Total used
            (
                {
                    'Employees Total': '111',
                    'Employees Total Indicator': EmployeesIndicator.ACTUAL,
                },
                (111, False),
            ),

            # (estimated) Employees Total used as Employees Here is not available
            (
                {
                    'Employees Total': '0',
                    'Employees Total Indicator': EmployeesIndicator.ESTIMATED,
                    'Employees Here': '0',
                    'Employees Here Indicator': EmployeesIndicator.NOT_AVAILABLE,
                },
                (0, True),
            ),

            # Not Available
            (
                {
                    'Employees Total': '0',
                    'Employees Total Indicator': EmployeesIndicator.NOT_AVAILABLE,
                    'Employees Here': '0',
                    'Employees Here Indicator': EmployeesIndicator.NOT_AVAILABLE,
                },
                (None, None),
            ),
            # Employees Total is not a number
            (
                {
                    'Employees Total': 'a',
                    'Employees Total Indicator': EmployeesIndicator.ESTIMATED,
                },
                (None, None),
            ),

            # Employees Total is empty
            (
                {
                    'Employees Total': '',
                    'Employees Total Indicator': EmployeesIndicator.ESTIMATED,
                },
                (None, None),
            ),

            # Employees Total Indicator is invalid
            (
                {
                    'Employees Total': '',
                    'Employees Total Indicator': 'a',
                },
                (None, None),
            ),

            # Employees Here is not a number
            (
                {
                    'Employees Total': '0',
                    'Employees Total Indicator': EmployeesIndicator.ESTIMATED,
                    'Employees Here': 'a',
                    'Employees Here Indicator': EmployeesIndicator.ESTIMATED,
                },
                (0, True),
            ),

            # Employees Here is empty
            (
                {
                    'Employees Total': '0',
                    'Employees Total Indicator': EmployeesIndicator.ESTIMATED,
                    'Employees Here': '',
                    'Employees Here Indicator': EmployeesIndicator.ESTIMATED,
                },
                (0, True),
            ),

            # Employees Here Indicator is invalid
            (
                {
                    'Employees Total': '0',
                    'Employees Total Indicator': EmployeesIndicator.ESTIMATED,
                    'Employees Here': '',
                    'Employees Here Indicator': 'a',
                },
                (0, True),
            ),

            # Indicator == NOT_AVAILABLE but Employees value != 0
            (
                {
                    'Employees Total': '1',
                    'Employees Total Indicator': EmployeesIndicator.NOT_AVAILABLE,
                },
                (None, None),
            ),
        ),
    )
    def test_success(self, wb_record, expected_output):
        """
        Test successful cases related to _extract_employees().
        """
        actual_output = extract_employees(wb_record)
        assert actual_output == expected_output


class TestExtractTurnover:
    """Tests for the _extract_turnover function."""

    @pytest.mark.parametrize(
        'wb_record,expected_output',
        (
            # Estimated
            (
                {
                    'Annual Sales in US dollars': '1',
                    'Annual Sales Indicator': TurnoverIndicator.ESTIMATED,
                },
                (1, True),
            ),

            # Modelled
            (
                {
                    'Annual Sales in US dollars': '1',
                    'Annual Sales Indicator': TurnoverIndicator.MODELLED,
                },
                (1, True),
            ),

            # Low end of range
            (
                {
                    'Annual Sales in US dollars': '1',
                    'Annual Sales Indicator': TurnoverIndicator.LOW_END_OF_RANGE,
                },
                (1, True),
            ),

            # Actual
            (
                {
                    'Annual Sales in US dollars': '111',
                    'Annual Sales Indicator': TurnoverIndicator.ACTUAL,
                },
                (111, False),
            ),

            # With scientific notation
            (
                {
                    'Annual Sales in US dollars': '1.03283E+11',
                    'Annual Sales Indicator': TurnoverIndicator.ESTIMATED,
                },
                (103283000000, True),
            ),

            # Float converted to int
            (
                {
                    'Annual Sales in US dollars': '1.5',
                    'Annual Sales Indicator': TurnoverIndicator.ESTIMATED,
                },
                (2, True),
            ),

            # Not available
            (
                {
                    'Annual Sales in US dollars': '0',
                    'Annual Sales Indicator': TurnoverIndicator.NOT_AVAILABLE,
                },
                (None, None),
            ),
            (
                {
                    'Annual Sales in US dollars': 'a',
                    'Annual Sales Indicator': TurnoverIndicator.ESTIMATED,
                },
                (None, None),
            ),

            # Annual Sales in US dollars is empty
            (
                {
                    'Annual Sales in US dollars': '',
                    'Annual Sales Indicator': TurnoverIndicator.ESTIMATED,
                },
                (None, None),
            ),

            # Annual Sales Indicator is invalid
            (
                {
                    'Annual Sales in US dollars': '1',
                    'Annual Sales Indicator': 'a',
                },
                (None, None),
            ),

            # Indicator == NOT_AVAILABLE but Annual Sales in US dollars value != 0
            (
                {
                    'Annual Sales in US dollars': '1',
                    'Annual Sales Indicator': TurnoverIndicator.NOT_AVAILABLE,
                },
                (None, None),
            ),
        ),
    )
    def test_success(self, wb_record, expected_output):
        """
        Test successful cases related to _extract_turnover().
        """
        actual_output = extract_turnover(wb_record)
        assert actual_output == expected_output


class TestExtractBusinessIndicator:
    @pytest.mark.parametrize('test_input,expected', [
        ('Y', True),
        ('N', False),
    ])
    def test_valid_data(self, test_input, expected):
        assert extract_business_indicator(test_input) == expected

    @pytest.mark.parametrize('test_input,exception,message', [
        ('', DataMappingError, 'no mapping for business indicator: '),
        ('X', DataMappingError, 'no mapping for business indicator: X'),
    ])
    def test_invalid_data(self, test_input, exception, message):
        with pytest.raises(exception) as ex:
            extract_business_indicator(test_input)

        assert str(ex.value) == message


class TestExtractLegalStatus:
    @pytest.mark.parametrize('test_input,expected', [
        ('0', LEGAL_STATUS_CODE_MAPPING[0].name),
        ('3', LEGAL_STATUS_CODE_MAPPING[3].name),
        ('9999', LegalStatusChoices.unknown.name),
        ('', LegalStatusChoices.unknown.name),
    ])
    def test_valid_data(self, test_input, expected):
        assert extract_legal_status(test_input) == expected


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
        (
            {
                'National Identification System Code': '999',
                'National Identification Number': 'a number',
            },
            [
                {
                    'registration_type': 'unmapped',
                    'original_registration_type': 999,
                    'original_registration_number': 'a number',
                    'original_registration_description': ''
                }
            ]
        ),
    ])
    def test_valid_data(self, test_input, expected):
        assert extract_registration_number(test_input) == expected


@pytest.mark.django_db
class TestExtractCompanyData:
    @pytest.mark.parametrize('raw_data,expected', [
        (
            {
                'DUNS Number': '1234567',
                'Business Name': 'Widgets Pty',
                'Secondary Name': 'Lots-a-widgets',
                'National Identification System Code': '12',
                'National Identification Number': '1234567',
                'Street Address': 'address 1',
                'Street Address 2': 'address 2',
                'City Name': 'city',
                'State/Province Name': 'county / area name',
                'State/Province Abbreviation': 'abr',
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
                'address_area_name': 'county / area name',
                'address_area_abbrev_name': 'abr',
                'address_county': 'county / area name',
                'address_postcode': 'postcode',
                'line_of_business': 'agriculture',
                'year_started': '2000',
                'global_ultimate_duns_number': '',
                'is_out_of_business': False,
                'legal_status': 'corporation',
                'is_employee_number_estimated': True,
                'employee_number': 5,
                'is_annual_sales_estimated': True,
                'annual_sales': 8.0,
                'address_country': 'GB',
                'industry_codes': [],
                'primary_industry_codes': []
            }
        ),
    ])
    def test_valid_data(self, raw_data, expected):
        assert extract_company_data(raw_data) == expected
