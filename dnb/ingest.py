import csv

from django.db.utils import DataError

from .models import Company


"""
CSV fields reference:

0: _DUNS_Number
1: DNB_REF_ID
2: DUNS
3: DUNS Recertification Code
4: Filler 1
5: DUNS Number
6: Business Name
7: Secondary Name
8: Registered Address Indicator
9: Street Address
10: Street Address 2
11: City Name
12: State/Province Name
13: Country Name
14: City Code
15: County Code
16: State/Province Code
17: State/Province Abbreviation
18: Country Code
19: Postal Code for Street Address
20: Continent Code
21: Mailing Address
22: Mailing City Name
23: Mailing County Name
24: Mailing State/Province Name
25: Mailing Country Name
26: Mailing City Code
27: Mailing County Code
28: Mailing State/Province Code
29: Mailing State/Province Abbreviation
30: Mailing Country Code
31: Postal Code For Mailing Address
32: Mailing Continent Code
33: National Identification Number
34: National Identification System Code
35: Country Telephone Access Code
36: Telephone Number
37: Cable Telex
38: Fax Number
39: Chief Executive Officer Name
40: Chief Executive Officer Title
41: Line of Business
42: US 1987 SIC 1
43: US 1987 SIC 2
44: US 1987 SIC 3
45: US 1987 SIC 4
46: US 1987 SIC 5
47: US 1987 SIC 6
48: Primary Local Activity Code
49: Activity Indicator
50: Year Started
51: Annual Sales Local
52: Annual Sales Indicator
53: Annual Sales in US dollars
54: Currency Code
55: Employees Here
56: Employees Here Indicator
57: Employees Total
58: Employees Total Indicator
59: Include Principles Indicator
60: Import/Export/ Agent Indicator
61: Legal Status
62: Control Indicator
63: Status Code
64: Subsidiary Code
65: Filler 2
66: Previous DUNS Number
67: Report Date
68: Filler 3
69: Headquarter/Parent DUNS Number
70: Headquarter/Parent Business Name
71: Headquarter/Parent Street Address
72: Headquarter/Parents City
73: Headquarter/Parent State/Province
74: Headquarter/Parent Country Name
75: Headquarter/Parents City Code
76: Headquarter/Parent County Code
77: Headquarter/Parent State/Province Abbreviation
78: Headquarter/Parent Country Code
79: Headquarter/Parent Postal Code
80: Headquarter/Parent Continent Code
81: Filler 4
82: Domestic Ultimate DUNS Number
83: Domestic Ultimate Business Name
84: Domestic Ultimate Street Address
85: Domestic Ultimate City Name
86: Domestic Ultimate State/Province Name
87: Domestic Ultimate City Code
88: Domestic Ultimate Country Code
89: Domestic Ultimate State Abbreviation
90: Domestic Ultimate Postal Code
91: Global Ultimate Indicator
92: Filler 5
93: Global Ultimate DUNS Number
94: Global Ultimate Name
95: Global Ultimate Street Address
96: Global Ultimate City Name
97: Global Ultimate State/Province
98: Global Ultimate Country Name
99: Global Ultimate City Code
100: Global Ultimate County Code
101: Ultimate State/Province Abbreviation
102: Global Ultimate Country Code
103: Global Ultimate Postal Code
104: Global Ultimate Continent Code
105: Number of Family Members
106: DIAS Code
107: Hierarchy Code
108: Family Update Date
109: Out of Business indicator
110: Marketable indicator
111: Delist indicator
"""


def to_int(index):
    def extract(data):
        value = data[index]

        return int(value) if value else None

    return extract


def to_bool(index, true_value, false_value):
    def extract(data):
        _map = {
            true_value: True,
            false_value: False,
        }

        return _map.get(data[index].upper(), None)

    return extract


def dnb_indicator_to_bool(index):
    """
    Available values:
    0 - actual
    1 - low end of the range
    2 - estimated (all records) or not available when sales is greater than zero (all records) or modeled (US records)
    3 - modeled (non US records)
    """

    # TODO: logic this needs to be reviewed.

    def extract(data):
        value = data[index]

        if value:
            return True if int(value) in [0, 1] else False
        else:
            return None

    return extract


class CompanyResource:

    MAPPING = {
        'duns_number': 5,
        'business_name': 6,
        'secondary_name': 7,
        'street_address': 9,
        'street_address2': 10,
        'city': 11,
        'state': 12,
        'country_name': 13,
        'country_code': to_int(18),
        'postal_code': 19,
        'national_id_number': 33,
        'national_id_code_type': 34,
        'line_of_business': 41,
        'is_out_of_business': to_bool(109, 'Y', 'N'),
        'year_started': to_int(50),
        'global_ultimate_duns_number': 93,
        'employee_number': 57,
        'is_employees_number_estimated': dnb_indicator_to_bool(58),
        'annual_sales': 53,
        'is_annual_sales_estimated': dnb_indicator_to_bool(52),
        'legal_status': 61,
        'status_code': 63,
    }

    def __init__(self, csv_row):

        self.data = self.extract(csv_row)
        self.errors = []

    @classmethod
    def extract(cls, raw_data):
        data = {}

        for name, elem in cls.MAPPING.items():
            if callable(elem):
                data[name] = elem(raw_data)
            else:
                data[name] = raw_data[elem]

        return data

    def is_valid(self):

        if not self.data['duns_number']:
            return False
        else:
            return True

    def get_or_create(self):

        assert self.is_valid()

        self.data['last_updated_source'] = Company.LAST_UPDATED_FILE

        return Company.objects.get_or_create(duns_number=self.data['duns_number'], defaults=self.data)


def ingest_csv(fd, logger):
    csv_reader = csv.reader(fd)

    stats = {
        'processed': 0,
        'failed': 0,
    }

    heading = True
    for row_number, row_data in enumerate(csv_reader, 1):
        assert len(row_data) == 112, f'incorrect number of rows on line {row_number}'

        if heading:
            heading = False
            continue

        company_resource = CompanyResource(row_data)

        if not company_resource.is_valid():
            logger.warning(f'Cannot import row {row_number}; row data: {row_data}')

            stats['failed'] += 1
        else:
            try:
                _, company = company_resource.get_or_create()
                stats['processed'] += 1
            except DataError:
                logger.exception('Cannot import row {row_number}; data {company_resource.data}')
                stats['failed'] += 1

    return stats
