import logging

from .constants import (BUSINESS_INDICATOR_MAPPING, DNB_COUNTRY_CODE_MAPPING,
                        LEGAL_STATUS_CODE_MAPPING, NATIONAL_ID_CODE_MAPPING)


class DataMappingError(Exception):
    pass


logger = logging.getLogger(__name__)


def dnb_country_lookup(dnb_country_code):
    """
    Takes a dnb country code and returns the associated iso alpha 2 code.

    It will raise an DataMappingException if: the code does not exist in the country code mapping or if the
    mapping entry does not have an associated iso alpha 2 code.  Not all DNB country codes map to iso 2 codes.
    """

    if dnb_country_code == '':
        return None

    if dnb_country_code not in DNB_COUNTRY_CODE_MAPPING:
        raise DataMappingError(f'{dnb_country_code} is not in mapping')

    iso_alpha2_code = DNB_COUNTRY_CODE_MAPPING[dnb_country_code]

    if not iso_alpha2_code:
        raise DataMappingError(f'{dnb_country_code} does not have an associated iso alpha 2 code')

    return iso_alpha2_code


def map_legal_status(legal_status_code):
    """Takes the worldbase legal status code and returns the """

    if legal_status_code == '' or int(legal_status_code) not in LEGAL_STATUS_CODE_MAPPING:
        raise DataMappingError(f'no mapping for legal status code: {legal_status_code}')

    return LEGAL_STATUS_CODE_MAPPING[int(legal_status_code)].name


def extract_registration_number(company_data):
    """
    Return the registration number and code, if present.
    """

    if company_data['National Identification System Code'] == '':
        return []

    national_id_code = int(company_data['National Identification System Code'])

    if national_id_code not in NATIONAL_ID_CODE_MAPPING:
        raise DataMappingError(f'National ID code {national_id_code} is not in mapping')

    registration_type = NATIONAL_ID_CODE_MAPPING[national_id_code].name

    return [
        {
            'registration_type': registration_type,
            'registration_number': company_data['National Identification Number'],
        }
    ]


def extract_employee_data(wb_data):
    return {
        'is_employees_number_estimated': False,
        'employee_number': 5,
    }


def extract_sales_data(wb_data):
    return {
        'is_annual_sales_estimated': False,
        'annual_sales': 8.00,
    }


def map_business_indicator(field_data):
    """
    Convert Y/N field into a boolean
    """

    try:
        return BUSINESS_INDICATOR_MAPPING[field_data]
    except KeyError:
        raise DataMappingError(f'no mapping for business indicator: {field_data}')


def extract_company_data(wb_data):
    """
    Process a single row of the worldbase file and return company data in a format suitable for insertion
    into the database.
    """

    company_data = {
        'duns_number': wb_data['DUNS'],
        'primary_name': wb_data['Business Name'],
        'trading_names': [wb_data['Secondary Name']] if wb_data['Secondary Name'] else [],
        'registration_numbers': extract_registration_number(wb_data),
        'address_line_1': wb_data['Street Address'],
        'address_line_2': wb_data['Street Address 2'],
        'address_town': wb_data['City Name'],
        'address_county': wb_data['State/Province Name'],
        'address_postcode': wb_data['Postal Code for Street Address'],
        'line_of_business': wb_data['Line of Business'],
        'year_started': int(wb_data['Year Started']) if wb_data['Year Started'] else None,
        'global_ultimate_duns_number': wb_data['Global Ultimate DUNS Number'],
        'is_out_of_business': map_business_indicator(wb_data['Out of Business indicator']),
        'legal_status': map_legal_status(wb_data['Legal Status']),
        **extract_employee_data(wb_data),
        **extract_sales_data(wb_data),
    }

    # We're currently only receiving UK company data but the company field is set to '000' (or 0 or '') which
    # indicates that the field is unspecified. For the time this field is being hard coded to the UK. An alternative
    # may be to use use country field instead of the DNB country code field.
    company_data['address_country'] = 'GB'

    return company_data
