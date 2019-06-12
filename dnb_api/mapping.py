from .constants import LEGAL_STATUS_MAPPING, OPERATING_STATUS_ACTIVE, REGISTRATION_NUMBER_TYPE_MAPPING


def extract_address(address_data):
    """Extract address fields from API response"""

    return {
        f'address_line_1': address_data.get('streetAddress', {}).get('line1', ''),
        f'address_line_2': address_data.get('streetAddress', {}).get('line2', ''),
        f'address_town': address_data.get('addressLocality', {}).get('name', ''),
        f'address_county': address_data.get('addressCounty', {}).get('name', ''),
        f'address_postcode': address_data.get('postalCode', ''),
        f'address_country': address_data.get('addressCountry', {}).get('isoAlpha2Code', ''),
    }

def extract_registered_address(company_data):

    if company_data['organization']['primaryAddress'].get('isRegisteredAddress', False):
        address = company_data['organization']['primaryAddress']
    else:
        address = company_data['organization']['registeredAddress']

    return {
        f'registered_{field}': value for field, value in address.items()
    }


def extract_registration_numbers(company_data):
    registration_numbers = []

    for registration_number in company_data['organization'].get('registrationNumbers', []):

        mapped_code = REGISTRATION_NUMBER_TYPE_MAPPING[registration_number['typeDnBCode']]
        assert mapped_code is not None, f'no mapping for {registration_number["typeDnBCode"]}'

        registration_numbers.append({
            'registration_type': mapped_code,
            'registration_number': registration_number['registrationNumber'],
        })

    return registration_numbers


def extract_legal_status(company_data):

    dnb_code = company_data['organization']['businessEntityType']['dnbCode']

    mapped_code = LEGAL_STATUS_MAPPING[dnb_code]

    return mapped_code


def extract_trading_names(company_data):
    trading_names = company_data['organization'].get('tradeStyleNames', [])

    return [item['name'] for item in trading_names]


def extract_is_out_of_business(company_data):
    """
    'isOutOfBusiness' is explicitly provided in search results.  In company detail data we have to extract the
    status from the 'operatingStatus' key.
    """

    status = company_data['organization']['dunsControlStatus']

    if 'isOutOfBusiness' in status:
        return status['isOutOfBusiness']
    elif 'operatingStatus' in status:
        return status['operatingStatus']['dnbCode'] != OPERATING_STATUS_ACTIVE
    else:
        raise ValueError('missing business status indicator')


def extract_company_data(company_data):
    """
    Extract company data from a single row of the Worldbase file
    """
    company = {
        'duns_number': company_data['organization']['duns'],
        'primary_name': company_data['organization']['primaryName'],
        'trading_names': extract_trading_names(company_data),
        'registration_numbers': extract_registration_numbers(company_data),
        # 'line_of_business': company_data['Line of Business'],   # not present in API data
        # 'year_started': company_data['Year Started'],   # not present in API data
        'global_ultimate_duns_number': company_data['organization']['corporateLinkage'].get('globalUltimate', {}).get('duns', ''),
        'is_out_of_business': extract_is_out_of_business(company_data),
        **extract_address(company_data['organization']['primaryAddress']),
        **extract_registered_address(company_data),
        'legal_status': extract_legal_status(company_data)
    }

    return company
