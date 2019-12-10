from collections import OrderedDict

import pytest

from company.constants import RegistrationNumberChoices
from company.models import Country
from company.serialisers import CompanySerialiser
from .factories import CompanyFactory, IndustryCodeFactory, PrimaryIndustryCodeFactory, RegistrationNumberFactory


@pytest.mark.django_db
def test_company_serialiser():
    company = CompanyFactory(**{
        'duns_number': '123456789',
        'primary_name': 'Test Company 1',
        'trading_names': ['ACME trading corp'],
        'global_ultimate_duns_number': '888888888',
        'global_ultimate_primary_name': 'global primary name',
        'domain': 'www.e-corp.corp',
        'is_out_of_business': False,
        'address_line_1': 'The Old Test Mill 1',
        'address_line_2': '100 Test Rd',
        'address_town': 'Cheshire',
        'address_county': 'address county',
        'address_postcode': 'address postcode',
        'address_country': Country.objects.get(iso_alpha2='GB'),
        'registered_address_line_1': 'reg address line 1',
        'registered_address_line_2': 'reg address line 2',
        'registered_address_town': 'reg address town',
        'registered_address_county': 'reg address county',
        'registered_address_country':  Country.objects.get(iso_alpha2='GB'),
        'registered_address_postcode': 'reg postcode',
        'annual_sales': 51806612000,
        'annual_sales_currency': 'USD',
        'is_annual_sales_estimated': None,
        'employee_number': 24,
        'year_started': 2000,
        'is_employees_number_estimated': False,
        'legal_status': 'foreign_company'
    })

    RegistrationNumberFactory(**{
        'company': company,
        'registration_type': RegistrationNumberChoices.uk_vat_number,
        'registration_number': '12341234',
    })

    IndustryCodeFactory(**{
        'company': company,
        'code': '517919',
        'description': 'All Other Telecommunications',
        'typeDescription': 'North American Industry Classification System 2017',
        'typeDnBCode': 30832,
        'priority': 2
    })

    IndustryCodeFactory(**{
        'company': company,
        'code': '423690',
        'description': 'Other Electronic Parts and Equipment Merchant Wholesalers',
        'typeDescription': 'North American Industry Classification System 2017',
        'typeDnBCode': 30832,
        'priority': 1
    })

    PrimaryIndustryCodeFactory(**{
        'company': company,
        'usSicV4': '5065',
        'usSicV4Description': 'Whol electronic parts/equipment'
    })

    assert CompanySerialiser(company).data == {
        'last_updated': None,
        'duns_number': '123456789',
        'primary_name': 'Test Company 1',
        'trading_names': ['ACME trading corp'],
        'registration_numbers': [
            OrderedDict(
                [
                    ('registration_type', 'VAT Registration number'),
                    ('registration_number', '12341234'),
                ]
            )
        ],
        'global_ultimate_duns_number': '888888888',
        'global_ultimate_primary_name': 'global primary name',
        'domain': 'www.e-corp.corp',
        'is_out_of_business': False,
        'address_line_1': 'The Old Test Mill 1',
        'address_line_2': '100 Test Rd',
        'address_town': 'Cheshire',
        'address_county': 'address county',
        'address_postcode': 'address postcode',
        'address_country': 'GB',
        'registered_address_line_1': 'reg address line 1',
        'registered_address_line_2': 'reg address line 2',
        'registered_address_town': 'reg address town',
        'registered_address_county': 'reg address county',
        'registered_address_country': 'GB',
        'registered_address_postcode': 'reg postcode',
        'annual_sales': 51806612000.0,
        'annual_sales_currency': 'USD',
        'is_annual_sales_estimated': None,
        'employee_number': 24,
        'is_employees_number_estimated': False,
        'primary_industry_codes': [
            OrderedDict([
                ('usSicV4', '5065'),
                ('usSicV4Description', 'Whol electronic parts/equipment'),
            ])
        ],
        'industry_codes': [
            OrderedDict(
                [
                    ('code', '423690'),
                    ('description', 'Other Electronic Parts and Equipment Merchant Wholesalers'),
                    ('priority', 1),
                    ('typeDescription', 'North American Industry Classification System 2017'),
                    ('typeDnBCode', '30832'),
                ]
            ),
            OrderedDict(
                [
                    ('code', '517919'),
                    ('description', 'All Other Telecommunications'),
                    ('priority', 2),
                    ('typeDescription', 'North American Industry Classification System 2017'),
                    ('typeDnBCode', '30832'),
                ]
            )
        ],
        'line_of_business': '',
        'year_started': 2000,
        'legal_status': 'foreign_company'
    }
