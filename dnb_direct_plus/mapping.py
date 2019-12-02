from company.constants import LegalStatusChoices
from .constants import (
    INFORMATION_SCOPE_CONSOLIDATED,
    LEGAL_STATUS_MAPPING,
    OPERATING_STATUS_ACTIVE,
    REGISTRATION_NUMBER_TYPE_MAPPING,
    RELIABILITY_CODE_ACTUAL,
)


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
        address = extract_address(company_data['organization']['primaryAddress'])
    elif 'registeredAddress' not in company_data['organization']:
        address = {}
    else:
        address = extract_address(company_data['organization']['registeredAddress'])

    return {
        f'registered_{field}': value for field, value in address.items()
    }


def extract_registration_numbers(company_data):
    registration_numbers = []

    for registration_number in company_data['organization'].get('registrationNumbers', []):
        if registration_number.get('typeDnBCode') in REGISTRATION_NUMBER_TYPE_MAPPING:
            mapped_code = REGISTRATION_NUMBER_TYPE_MAPPING[registration_number['typeDnBCode']].name

            registration_numbers.append({
                'registration_type': mapped_code,
                'registration_number': registration_number['registrationNumber'],
            })
        else:
            registration_numbers.append({
                'registration_type': 'unmapped',
                'original_registration_type': registration_number.get('typeDnBCode'),
                'original_registration_number': registration_number['registrationNumber'],
                'original_registration_description': registration_number['typeDescription'],
            })

    return registration_numbers


def extract_legal_status(company_data):

    local_code = LegalStatusChoices.unknown.name

    try:
        dnb_code = company_data['organization']['businessEntityType']['dnbCode']
        local_code = LEGAL_STATUS_MAPPING[dnb_code].name
    except KeyError:
        pass

    return local_code


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


def extract_employee_numbers(company_data):
    employee_number_entries = company_data['organization'].get('numberOfEmployees')

    if not employee_number_entries:
        return None, None

    employee_data = None

    if len(employee_number_entries) > 0:
        for entry in employee_number_entries:
            if entry.get('informationScopeDnBCode') == INFORMATION_SCOPE_CONSOLIDATED:
                employee_data = entry
                break

    if not employee_data:
        employee_data = employee_number_entries[0]

    is_estimated = employee_data.get('reliabilityDnBCode') != RELIABILITY_CODE_ACTUAL

    return is_estimated, employee_data['value']


def extract_annual_sales(company_data):
    try:
        data = company_data['organization']['financials'][0]['yearlyRevenue'][0]

        return data['currency'], data['value']
    except (KeyError, IndexError):
        return None, None


def extract_company_data(company_data):

    is_employees_number_estimated, employee_number = extract_employee_numbers(company_data)
    annual_sales_currency, annual_sales = extract_annual_sales(company_data)

    company = {
        'duns_number': company_data['organization']['duns'],
        'primary_name': company_data['organization']['primaryName'],
        'trading_names': extract_trading_names(company_data),
        'registration_numbers': extract_registration_numbers(company_data),
        'global_ultimate_duns_number':
            company_data['organization']['corporateLinkage'].get('globalUltimate', {}).get('duns', ''),
        'global_ultimate_primary_name':
            company_data['organization']['corporateLinkage'].get('globalUltimate', {}).get('primaryName', ''),
        'domain': company_data['organization'].get('domain', None),
        'is_out_of_business': extract_is_out_of_business(company_data),
        **extract_address(company_data['organization']['primaryAddress']),
        **extract_registered_address(company_data),
        'annual_sales': annual_sales,
        'annual_sales_currency': annual_sales_currency,
        'is_annual_sales_estimated': None,  # The API does not supply this data
        'employee_number': employee_number,
        'is_employees_number_estimated': is_employees_number_estimated,
        'primary_industry_codes': company_data['organization'].get('primaryIndustryCodes', []),
        'industry_codes': company_data['organization'].get('industryCodes', []),
        'legal_status': extract_legal_status(company_data),
        'year_started': None,
    }

    return company
