import logging

from decimal import Decimal, InvalidOperation

from company.constants import LegalStatusChoices
from .constants import (
    BUSINESS_INDICATOR_MAPPING,
    DNB_COUNTRY_CODE_MAPPING,
    EmployeesIndicator,
    LEGAL_STATUS_CODE_MAPPING,
    NATIONAL_ID_CODE_MAPPING,
    TurnoverIndicator,
)


logger = logging.getLogger(__name__)


def extract_employees(wb_record):
    """
    Returns a tuple with number of employees as an int and a bool indicating
    if that value is estimated or not.
    The data is extracted from the 'Employees Total' field in the Worldbase record
    if defined or 'Employees Here' otherwise.
    None values are returned if the data is not available.
    """

    employees_indicator, number_of_employees = None, None

    try:
        number_of_employees = int(wb_record['Employees Total'])
        employees_indicator = EmployeesIndicator(wb_record['Employees Total Indicator'])
    except (ValueError, KeyError):

        try:
            number_of_employees = int(wb_record['Employees Here'])
            employees_indicator = EmployeesIndicator(wb_record['Employees Here Indicator'])
        except (ValueError, KeyError):
            pass

    if number_of_employees is None or employees_indicator is None or \
                    employees_indicator == EmployeesIndicator.NOT_AVAILABLE:
        return None, None

    is_number_of_employees_estimated = employees_indicator != EmployeesIndicator.ACTUAL

    return number_of_employees, is_number_of_employees_estimated


def extract_turnover(wb_record):
    """
    Returns a tuple with the turnover as an int and a bool indicating if the value
    is estimated or not.
    None values are returned if the data is not available in the Worldbase record.
    """

    try:
        turnover_indicator = TurnoverIndicator(wb_record['Annual Sales Indicator'])
        turnover = round(Decimal(wb_record['Annual Sales in US dollars']))
    except (InvalidOperation, ValueError, KeyError):
        return None, None

    if turnover_indicator == turnover_indicator.NOT_AVAILABLE:
        return None, None

    is_number_of_employees_estimated = turnover_indicator != turnover_indicator.ACTUAL
    return turnover, is_number_of_employees_estimated


def dnb_country_lookup(dnb_country_code):
    """
    Takes a dnb country code and returns the associated iso alpha 2 code.

    It will raise an DataMappingException if: the code does not exist in the country code mapping or if the
    mapping entry does not have an associated iso alpha 2 code.  Not all DNB country codes map to iso 2 codes.
    """

    if dnb_country_code == '':
        return None

    if dnb_country_code not in DNB_COUNTRY_CODE_MAPPING:
        raise IndexError(f'Country code {dnb_country_code} is not in mapping')

    iso_alpha2_code = DNB_COUNTRY_CODE_MAPPING[dnb_country_code]

    if not iso_alpha2_code:
        raise IndexError(f'Country code {dnb_country_code} does not have an associated iso alpha 2 code')

    return iso_alpha2_code


def extract_legal_status(legal_status_code):
    """Takes the worldbase status code and returns the local status code value"""

    local_code = LegalStatusChoices.unknown.name

    try:
        local_code = LEGAL_STATUS_CODE_MAPPING[int(legal_status_code)].name
    except (KeyError, ValueError):
        logger.warning(f'DNB legal code: {legal_status_code} has no local mapping')

    return local_code


def extract_registration_number(company_data):
    """
    Return the registration number and code, if present.
    """

    try:
        national_id_number = company_data['National Identification Number']
        national_id_code = int(company_data['National Identification System Code'])
    except ValueError:
        return []

    if national_id_code in NATIONAL_ID_CODE_MAPPING:
        registration_type = NATIONAL_ID_CODE_MAPPING[national_id_code].name

        registration_numbers = [
            {
                'registration_type': registration_type,
                'registration_number': national_id_number,
            }
        ]
    else:
        registration_numbers = [{
            'registration_type': 'unmapped',
            'original_registration_type': national_id_code,
            'original_registration_number': national_id_number,
            'original_registration_description': '',
        }]

    return registration_numbers


def extract_business_indicator(field_data):
    """
    Convert Y/N field into a boolean
    """

    try:
        return BUSINESS_INDICATOR_MAPPING[field_data]
    except KeyError:
        raise IndexError(f'no mapping for business indicator: {field_data}')


def extract_company_data(wb_data):
    """
    Process a single row of the worldbase file and return company data in a format suitable for insertion
    into the database.
    """

    employee_number, is_employee_number_estimated = extract_employees(wb_data)
    annual_sales, is_annual_sales_estimated = extract_turnover(wb_data)

    company_data = {
        'duns_number': wb_data['DUNS Number'],
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
        'is_out_of_business': extract_business_indicator(wb_data['Out of Business indicator']),
        'legal_status': extract_legal_status(wb_data['Legal Status']),
        'employee_number': employee_number,
        'is_employee_number_estimated': is_employee_number_estimated,
        'annual_sales': annual_sales,
        'is_annual_sales_estimated': is_annual_sales_estimated,
        'primary_industry_codes': [],
        'industry_codes': [],
    }

    return company_data
