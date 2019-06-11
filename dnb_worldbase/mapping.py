from decimal import Decimal
from enum import Enum

from .constants import (BUSINESS_INDICATOR_MAPPING, DNB_COUNTRY_CODE_MAPPING,
                        LEGAL_STATUS_CODE_MAPPING, NATIONAL_ID_CODE_MAPPING)


class DataMappingError(Exception):
    pass


class EmployeesIndicator(Enum):
    """
    Indicates if the field Employees Total/Here is an actual value,
    estimated value or not available.
    """

    NOT_AVAILABLE = ''
    ACTUAL = '0'
    LOW_END_OF_RANGE = '1'
    ESTIMATED = '2'
    MODELLED = '3'


class TurnoverIndicator(Enum):
    """
    Indicates if the field 'Annual Sales in US dollars' is an actual value,
    estimated value or not available.
    """

    NOT_AVAILABLE = ''
    ACTUAL = '0'
    LOW_END_OF_RANGE = '1'
    ESTIMATED = '2'
    MODELLED = '3'


class OutOfBusinessIndicator(Enum):
    """Indicates if a business is out of business."""

    OUT_OF_BUSINESS = 'Y'
    NOT_OUT_OF_BUSINESS = 'N'


def extract_employees(wb_record):
    """
    Returns a tuple with number of employees as an int and a bool indicating
    if that value is estimated or not.
    The data is extracted from the 'Employees Total' field in the Worldbase record
    if defined or 'Employees Here' otherwise.
    None values are returned if the data is not available in the Worldbase record.
    :returns: (number_of_employees, is_number_of_employees_estimated) for the
        given D&B Worldbase record or (None, None) if the data is not available in the record
    """
    number_of_employees = int(wb_record['Employees Total'])
    employees_indicator = EmployeesIndicator(wb_record['Employees Total Indicator'])

    if not number_of_employees:
        employees_here_indicator = EmployeesIndicator(wb_record['Employees Here Indicator'])
        if employees_here_indicator != EmployeesIndicator.NOT_AVAILABLE:
            number_of_employees = int(wb_record['Employees Here'])
            employees_indicator = employees_here_indicator

    if employees_indicator == EmployeesIndicator.NOT_AVAILABLE:
        assert not number_of_employees

        return None, None

    is_number_of_employees_estimated = employees_indicator != EmployeesIndicator.ACTUAL

    return number_of_employees, is_number_of_employees_estimated


def extract_turnover(wb_record):
    """
    Returns a tuple with the turnover as an int and a bool indicating if the value
    is estimated or not.
    None values are returned if the data is not available in the Worldbase record.
    :returns: (turnover, is_turnover_estimated) for the given D&B Worldbase record
        or (None, None) if the data is not available in the record
    """
    turnover = round(Decimal(wb_record['Annual Sales in US dollars']))
    turnover_indicator = TurnoverIndicator(wb_record['Annual Sales Indicator'])

    if turnover_indicator == turnover_indicator.NOT_AVAILABLE:
        assert not turnover

        return None, None

    is_turnover_estimated = turnover_indicator != turnover_indicator.ACTUAL

    return turnover, is_turnover_estimated


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
    """Takes the worldbase status code and returns the local status code value"""

    if legal_status_code == '' or legal_status_code not in LEGAL_STATUS_CODE_MAPPING:
        raise DataMappingError(f'no mapping for legal status code: {legal_status_code}')

    return LEGAL_STATUS_CODE_MAPPING[legal_status_code].name


def extract_registration_number(company_data):
    """
    Return the registration number and code, if present.
    """

    if company_data['National Identification System Code'] == '':
        return []

    national_id_code = company_data['National Identification System Code']

    if national_id_code not in NATIONAL_ID_CODE_MAPPING:
        raise DataMappingError(f'National ID code {national_id_code} is not in mapping')

    registration_type = NATIONAL_ID_CODE_MAPPING[national_id_code].name

    return [
        {
            'registration_type': registration_type,
            'registration_number': company_data['National Identification Number'],
        }
    ]


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

    employee_number, is_employee_number_estimated = extract_employees(wb_data)
    annual_sales, is_annual_sales_estimated = extract_turnover(wb_data)

    company_data = {
        'duns_number': wb_data['DUNS'],
        'primary_name': wb_data['Business Name'],
        'trading_names': [wb_data['Secondary Name']] if wb_data['Secondary Name'].strip() else [],
        'registration_numbers': extract_registration_number(wb_data),
        'address_line_1': wb_data['Street Address'],
        'address_line_2': wb_data['Street Address 2'],
        'address_town': wb_data['City Name'],
        'address_county': wb_data['State/Province Name'],
        'address_country': dnb_country_lookup(wb_data['Country Code']),
        'address_postcode': wb_data['Postal Code for Street Address'],
        'line_of_business': wb_data['Line of Business'],
        'year_started': wb_data['Year Started'],
        'global_ultimate_duns_number': wb_data['Global Ultimate DUNS Number'],
        'is_out_of_business': map_business_indicator(wb_data['Out of Business indicator']),
        'legal_status': map_legal_status(wb_data['Legal Status']),
        'employee_number': employee_number,
        'is_employee_number_estimated': is_employee_number_estimated,
        'annual_sales': annual_sales,
        'is_annual_sales_estimated': is_annual_sales_estimated,
    }

    return company_data
