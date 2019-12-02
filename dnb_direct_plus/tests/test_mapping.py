import json

import pytest

from ..constants import (
    OPERATING_STATUS_ACTIVE
)

from ..mapping import (
    extract_address,
    extract_annual_sales,
    extract_company_data,
    extract_employee_numbers,
    extract_is_out_of_business,
    extract_legal_status,
    extract_registered_address,
    extract_registration_numbers,
    extract_trading_names,
)


@pytest.mark.parametrize('input_data, expected', [
    # full address without a prefix
    (
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
    (
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
    # no fields are required
    (
        {
        },
        {
            'address_line_1': '',
            'address_line_2': '',
            'address_town': '',
            'address_county': '',
            'address_postcode': '',
            'address_country': ''
        }
    ),
])
def test_extract_address(input_data, expected):
    assert extract_address(input_data) == expected


@pytest.mark.parametrize('input_data, expected', [
    # all empty
    (
        {
            'organization': {
                'primaryAddress': {},
                'registeredAddress': {}
            }
        },
        {
            'registered_address_line_1': '',
            'registered_address_line_2': '',
            'registered_address_town': '',
            'registered_address_county': '',
            'registered_address_postcode': '',
            'registered_address_country': ''
        }
    ),
    # isRegisteredAddress is True, use primaryAddress
    (
        {
            'organization': {
                'primaryAddress': {
                    'isRegisteredAddress': True,
                    'addressCountry': {
                        'isoAlpha2Code': 'GB',
                    },
                    'postalCode': 'LS10 2UR',
                    'streetAddress': {
                        'line1': 'Acme Ltd',
                        'line2': 'Acme Ind. Park'
                    },
                    'addressLocality': {
                        'name': 'Manchester'
                    },
                    'addressCounty': {
                        'name': 'Greater Manchester'
                    }
                }
            }
        },
        {
            'registered_address_line_1': 'Acme Ltd',
            'registered_address_line_2': 'Acme Ind. Park',
            'registered_address_town': 'Manchester',
            'registered_address_county': 'Greater Manchester',
            'registered_address_postcode': 'LS10 2UR',
            'registered_address_country': 'GB'
        }
    ),
    # isRegisteredAddress not set, use registeredAddress
    (
        {
            'organization': {
                'primaryAddress': {
                    'addressCountry': {
                        'isoAlpha2Code': 'GB',
                    },
                    'postalCode': 'LS10 2UR',
                    'streetAddress': {
                    }
                },
                'registeredAddress': {
                    'addressCountry': {
                        'isoAlpha2Code': 'US',
                    },
                    'postalCode': 'M3 1NL',
                    'streetAddress': {
                    }
                }
            }
        },
        {
            'registered_address_line_1': '',
            'registered_address_line_2': '',
            'registered_address_town': '',
            'registered_address_county': '',
            'registered_address_postcode': 'M3 1NL',
            'registered_address_country': 'US'
        }
    ),
    # isRegisteredAddress is False, use registeredAddress field
    (
        {
            'organization': {
                'primaryAddress': {
                    'isRegisteredAddress': False,
                    'addressCountry': {
                        'isoAlpha2Code': 'GB',
                    },
                    'postalCode': 'LS10 2UR',
                    'streetAddress': {
                        'line1': 'Acme Ltd',
                        'line2': 'Acme Ind. Park'
                    },
                    'addressLocality': {
                        'name': 'Manchester'
                    },
                    'addressCounty': {
                        'name': 'Greater Manchester'
                    }
                },
                'registeredAddress': {
                    'addressCountry': {
                        'isoAlpha2Code': 'US',
                    },
                    'postalCode': 'M3 1NL',
                    'streetAddress': {
                    }
                }
            }
        },
        {
            'registered_address_line_1': '',
            'registered_address_line_2': '',
            'registered_address_town': '',
            'registered_address_county': '',
            'registered_address_postcode': 'M3 1NL',
            'registered_address_country': 'US'
        }
    )
])
def test_extract_registered_address(input_data, expected):
    assert extract_registered_address(input_data) == expected


@pytest.mark.parametrize('input_data, expected', [
    # empty
    (
        {
            'organization': {
            }
        },
        []
    ),
    # mapped
    (
        {
            'organization': {
                'registrationNumbers': [
                    {
                        'typeDnBCode': 2541,
                        'registrationNumber': '123456789',
                        'typeDescription': ''
                    }
                ]
            }
        },
        [
            {
                'registration_type': 'uk_companies_house_number',
                'registration_number': '123456789',
            }
        ]
    ),
    # unmapped
    (
        {
            'organization': {
                'registrationNumbers': [
                    {
                        'typeDnBCode': 'FAKE-CODE',
                        'registrationNumber': '123456789',
                        'typeDescription': 'This is not a real code'
                    }
                ]
            }
        },
        [
            {
                'registration_type': 'unmapped',
                'original_registration_type': 'FAKE-CODE',
                'original_registration_number': '123456789',
                'original_registration_description': 'This is not a real code'
            }
        ]
    ),
    # partial data
    (
        {
            'organization': {
                'registrationNumbers': [
                    {
                        'registrationNumber': '123456789',
                        'typeDescription': 'This is not a real code'
                    }
                ]
            }
        },
        [
            {
                'registration_type': 'unmapped',
                'original_registration_type': None,
                'original_registration_number': '123456789',
                'original_registration_description': 'This is not a real code'
            }
        ]
    ),
])
def test_extract_registration_numbers(input_data, expected):
    assert extract_registration_numbers(input_data) == expected


@pytest.mark.parametrize('input_data, expected', [
    (
        # empty
        {
            'organization': {
            }
        },
        'unknown'
    ),
    (
        # invalid/unmapped code
        {
            'organization': {
                'businessEntityType': {
                    'dnbCode': 999999
                }
            }
        },
        'unknown'
    ),
    (
        # corporation
        {
            'organization': {
                'businessEntityType': {
                    'dnbCode': 451
                }
            }
        },
        'corporation'
    ),
])
def test_extract_legal_status(input_data, expected):
    extract_legal_status(input_data) == expected


@pytest.mark.parametrize('input_data, expected', [
    (
        {
            'organization': {},
        },
        []
    ),
    (
        {
            'organization': {
                'tradeStyleNames': [
                    {
                        'name': 'Acme Inc.',
                    },
                    {
                        'name': 'Acme Plc.',
                    }
                ],
            },
        },
        ['Acme Inc.', 'Acme Plc.']
    )
])
def test_extract_trading_names(input_data, expected):
    extract_trading_names(input_data) == expected


@pytest.mark.parametrize('input_data, expected', [
    # company search result - trading
    (
        {
            'organization': {
                'dunsControlStatus': {
                    'isOutOfBusiness': False
                }
            }
        },
        False
    ),
    # company search result - out of business
    (
        {
            'organization': {
                'dunsControlStatus': {
                    'isOutOfBusiness': True
                }
            }
        },
        True
    ),
    #  cmplelk detail result - trading
    (
        {
            'organization': {
                'dunsControlStatus': {
                    'operatingStatus': {
                        'dnbCode': OPERATING_STATUS_ACTIVE
                    }
                }
            }
        },
        False
    ),
    #  cmplelk detail result - out of business
    (
        {
            'organization': {
                'dunsControlStatus': {
                    'operatingStatus': {
                        'dnbCode': OPERATING_STATUS_ACTIVE + 1000
                    }
                }
            }
        },
        True
    )
])
def test_extract_is_out_of_business(input_data, expected):
    extract_is_out_of_business(input_data) == expected


def test_extract_is_out_of_business_bad_data():
    bad_data = {
        'organization': {
            'dunsControlStatus': {

            }
        }
    }
    with pytest.raises(ValueError):
        extract_is_out_of_business(bad_data)


@pytest.mark.parametrize('input_data, expected', [
    # multiple entries, use the consolidated field
    (
        {
            'organization': {
                'numberOfEmployees': [
                    {
                        'value': 4000,
                        'informationScopeDescription': 'Headquarters Only (Employs Here)',
                        'informationScopeDnBCode': 9068,
                        'reliabilityDescription': 'Actual',
                        'reliabilityDnBCode': 9092
                    },
                    {
                        'value': 33000,
                        'informationScopeDescription': 'Consolidated',
                        'informationScopeDnBCode': 9067,
                        'reliabilityDescription': 'Actual',
                        'reliabilityDnBCode': 9092
                    }
                ]
            }
        },
        (False, 33000)
    ),
    # multiple entries, no consolidated field, use the first field
    (
        {
            'organization': {
                'numberOfEmployees': [
                    {
                        'value': 4000,
                        'informationScopeDescription': 'Headquarters Only (Employs Here)',
                        'informationScopeDnBCode': 9068,
                        'reliabilityDescription': 'Actual',
                        'reliabilityDnBCode': 9092
                    },
                    {
                        'value': 33000,
                        'informationScopeDescription': 'Not-conslidated',
                        'informationScopeDnBCode': 9999,
                        'reliabilityDescription': 'Actual',
                        'reliabilityDnBCode': 9092
                    }
                ]
            }
        },
        (False, 4000)
    ),
    # single entry
    (
        {
            'organization': {
                'numberOfEmployees': [
                    {
                        'value': 4000,
                        'informationScopeDescription': 'Headquarters Only (Employs Here)',
                        'informationScopeDnBCode': 9068,
                        'reliabilityDescription': 'Actual',
                        'reliabilityDnBCode': 9999
                    }
                ]
            }
        },
        (True, 4000)
    ),
    # missing data
    (
        {
            'organization': {}
        },
        (None, None)
    ),
    # missing reliabilityDnbCode
    (
        {
            'organization': {
                'numberOfEmployees': [
                    {
                        'value': 4000,
                        'informationScopeDescription': 'Headquarters Only (Employs Here)',
                        'informationScopeDnBCode': 9068,
                        'reliabilityDescription': 'Actual',
                    }
                ]
            }
        },
        (True, 4000)
    ),
    # missing data
    (
        {
            'organization': {
                'numberOfEmployees': []
            }
        },
        (None, None)
    ),
])
def test_extract_employee_numbers(input_data, expected):
    assert extract_employee_numbers(input_data) == expected


@pytest.mark.parametrize('input_data, expected', [
    (
        {
            'organization': {
                'financials': [
                    {
                        'yearlyRevenue': [
                            {
                                'value': 51806612000,
                                'currency': 'USD'
                            }
                        ]
                    }
                ]
            }
        },
        ('USD', 51806612000)
    ),
    (
        {
            'organization': {
                'financials': [
                    {
                        'yearlyRevenue': [
                        ]
                    }
                ]
            }
        },
        (None, None)
    )
])
def test_extract_annual_sales(input_data, expected):
    assert extract_annual_sales(input_data) == expected


def test_company_list_ingest(company_list_api_response_json):

    company_data = json.loads(company_list_api_response_json)
    extracted_data = extract_company_data(company_data['searchCandidates'][0])

    assert extracted_data == {
        'duns_number': '123456789',
        'primary_name': 'Test Company 1',
        'trading_names': [],
        'registration_numbers': [
            {
                'registration_type': 'unmapped',
                'original_registration_type': 1358,
                'original_registration_number': 'F-11111',
                'original_registration_description': 'Company Registry Identification Number (HK)'
            }
        ],
        'global_ultimate_duns_number': '',
        'global_ultimate_primary_name': '',
        'domain': None,
        'is_out_of_business': False,
        'address_line_1': 'The Old Test Mill 1',
        'address_line_2': '100 Test Rd',
        'address_town': 'Cheshire',
        'address_county': '',
        'address_postcode': '',
        'address_country': 'GB',
        'annual_sales': 51806612000,
        'annual_sales_currency': 'USD',
        'is_annual_sales_estimated': None,
        'employee_number': 24,
        'is_employees_number_estimated': False,
        'primary_industry_codes': [
            {
                'usSicV4': '5065',
                'usSicV4Description': 'Whol electronic parts/equipment'
            }
        ],
        'industry_codes': [
            {
                'code': '517919',
                'description': 'All Other Telecommunications',
                'typeDescription': 'North American Industry Classification System 2017',
                'typeDnbCode': 30832,
                'priority': 2
            },
            {
                'code': '423690',
                'description': 'Other Electronic Parts and Equipment Merchant Wholesalers',
                'typeDescription': 'North American Industry Classification System 2017',
                'typeDnbCode': 30832,
                'priority': 1
            }
        ],
        'year_started': None,
        'legal_status': 'foreign_company'
    }


def test_cmpelk_ingest(cmpelk_api_response_json):
    company_data = json.loads(cmpelk_api_response_json)
    extracted_data = extract_company_data(company_data)

    assert extracted_data == {
        'duns_number': '987654321',
        'primary_name': 'Test Company, Inc.',
        'trading_names': [],
        'registration_numbers': [],
        'global_ultimate_duns_number': '12345679',
        'global_ultimate_primary_name': 'Test Company, Inc.',
        'domain': None,
        'is_out_of_business': False,
        'address_line_1': '492 Koller St',
        'address_line_2': None,
        'address_town': 'San Francisco',
        'address_county': 'San Francisco',
        'address_postcode': '94110',
        'address_country': 'US',
        'registered_address_line_1': '',
        'registered_address_line_2': '',
        'registered_address_town': '',
        'registered_address_county': '',
        'registered_address_postcode': '',
        'registered_address_country': '',
        'annual_sales': 22589957,
        'annual_sales_currency': 'USD',
        'is_annual_sales_estimated': None,
        'employee_number': 153,
        'is_employees_number_estimated': False,
        'primary_industry_codes': [],
        'industry_codes': [
            {
                'code': '323111',
                'description': 'Commercial Printing (except Screen and Books)',
                'typeDescription': 'North American Industry Classification System 2017',
                'typeDnBCode': 30832,
                'priority': 1
            }
        ],
        'year_started': None,
        'legal_status': 'corporation'
    }
