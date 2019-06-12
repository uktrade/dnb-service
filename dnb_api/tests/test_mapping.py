import os
import json

import pytest

from ..mapping import extract_company_data, extract_address


@pytest.fixture(scope="module")
def full_api_data():
    with open(os.path.join(os.path.dirname(__file__), 'api_data/company_detail.json')) as f:
        return json.loads(f.read())


@pytest.fixture(scope="module")
def search_api_data():
    with open(os.path.join(os.path.dirname(__file__), 'api_data/company_search.json')) as f:
        return json.loads(f.read())


@pytest.mark.parametrize('prefix, input_data, expected', [
    # full address without a prefix
    (
        '',
        {
            'addressCountry': {
                'isoAlpha2Code': 'GB',
            },
            'addressLocality': {
                'name': 'LEEDS'
            },
            'addressRegion': {},
            'addressCounty': {
                'name': 'West Yorkshire',
            },
            'postalCode': 'LS10 2UR',
            'streetAddress': {
                'line1': 'Leeds street',
                'line2': 'Leeds area'
            },
        },
        {
            'address_line_1': 'Leeds street',
            'address_line_2': 'Leeds area',
            'address_town': 'LEEDS',
            'address_county': 'West Yorkshire',
            'address_postcode': 'LS10 2UR',
            'address_country': 'GB'
        }
    ),
    # with prefix
    (
        'test_',
        {
            'addressCountry': {
                'isoAlpha2Code': 'GB',
            },
            'addressLocality': {
                'name': 'LEEDS'
            },
            'addressRegion': {},
            'addressCounty': {
                'name': 'West Yorkshire',
            },
            'postalCode': 'LS10 2UR',
            'streetAddress': {
                'line1': 'Leeds street',
                'line2': 'Leeds area'
            },
        },
        {
            'test_address_line_1': 'Leeds street',
            'test_address_line_2': 'Leeds area',
            'test_address_town': 'LEEDS',
            'test_address_county': 'West Yorkshire',
            'test_address_postcode': 'LS10 2UR',
            'test_address_country': 'GB'
        }
    ),
    (
        '',
        {
            'addressCountry': {
                'isoAlpha2Code': 'GB',
            },
            'postalCode': 'LS10 2UR',
            'streetAddress': {
            },
        },
        {
            'address_line_1': '',
            'address_line_2': '',
            'address_town': '',
            'address_county': '',
            'address_postcode': 'LS10 2UR',
            'address_country': 'GB'
        }
    ),

])
def test_extract_address(prefix, input_data, expected):
    assert extract_address(prefix, input_data) == expected


# class TestExtractRegistrationNumbers:



def test_ingest_full(full_api_data):
    company_data = extract_company_data(full_api_data)
