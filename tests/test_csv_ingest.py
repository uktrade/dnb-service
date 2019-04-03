import pytest

from dnb.ingest import CompanyResource, dnb_indicator_to_bool, to_bool, to_int
from dnb.models import Company

TEST_ROW_DATA = [
    '_DUNS_Number',
    'DNB_REF_ID',
    'DUNS',
    'DUNS Recertification Code',
    'Filler 1',
    '123456',
    'Business Name',
    'Secondary Name',
    'Registered Address Indicator',
    'Street Address',
    'Street Address 2',
    'City Name',
    'State/Province Name',
    'Country Name',
    'City Code',
    '012',
    'State/Province Code',
    'State/Province Abbreviation',
    '357',
    'sw1a 2aw',
    'Continent Code',
    'Mailing Address',
    'Mailing City Name',
    'Mailing County Name',
    'Mailing State/Province Name',
    'Mailing Country Name',
    'Mailing City Code',
    'Mailing County Code',
    'Mailing State/Province Code',
    'Mailing State/Province Abbreviation',
    'Mailing Country Code',
    'Postal Code For Mailing Address',
    'Mailing Continent Code',
    '086572',
    '00012',
    'Country Telephone Access Code',
    'Telephone Number',
    'Cable Telex',
    'Fax Number',
    'Chief Executive Officer Name',
    'Chief Executive Officer Title',
    'Line of Business',
    'US 1987 SIC 1',
    'US 1987 SIC 2',
    'US 1987 SIC 3',
    'US 1987 SIC 4',
    'US 1987 SIC 5',
    'US 1987 SIC 6',
    'Primary Local Activity Code',
    'Activity Indicator',
    '2000',
    'Annual Sales Local',
    '0',
    '5000',
    'Currency Code',
    'Employees Here',
    'Employees Here Indicator',
    '5000',
    '2',
    'Include Principles Indicator',
    'Import/Export/ Agent Indicator',
    '018',
    'Control Indicator',
    '4',
    'Subsidiary Code',
    'Filler 2',
    'Previous DUNS Number',
    'Report Date',
    'Filler 3',
    'Headquarter/Parent DUNS Number',
    'Headquarter/Parent Business Name',
    'Headquarter/Parent Street Address',
    'Headquarter/Parents City',
    'Headquarter/Parent State/Province',
    'Headquarter/Parent Country Name',
    'Headquarter/Parents City Code',
    'Headquarter/Parent County Code',
    'Headquarter/Parent State/Province Abbreviation',
    'Headquarter/Parent Country Code',
    'Headquarter/Parent Postal Code',
    'Headquarter/Parent Continent Code',
    'Filler 4',
    'Domestic Ultimate DUNS Number',
    'Domestic Ultimate Business Name',
    'Domestic Ultimate Street Address',
    'Domestic Ultimate City Name',
    'Domestic Ultimate State/Province Name',
    'Domestic Ultimate City Code',
    'Domestic Ultimate Country Code',
    'Domestic Ultimate State Abbreviation',
    'Domestic Ultimate Postal Code',
    'Global Ultimate Indicator',
    'Filler 5',
    '013',
    'Global Ultimate Name',
    'Global Ultimate Street Address',
    'Global Ultimate City Name',
    'Global Ultimate State/Province',
    'Global Ultimate Country Name',
    'Global Ultimate City Code',
    'Global Ultimate County Code',
    'Ultimate State/Province Abbreviation',
    'Global Ultimate Country Code',
    'Global Ultimate Postal Code',
    'Global Ultimate Continent Code',
    'Number of Family Members',
    'DIAS Code',
    'Hierarchy Code',
    'Family Update Date',
    'N',
    'Marketable indicator',
    'Delist indicator'
]


def test_to_int_integer():
    assert to_int(0)(['1234']) == 1234


def test_to_int_integer_empty():
    assert not to_int(0)([''])


@pytest.mark.parametrize('test_input,expected', [
    ('Y', True),
    ('N', False),
    ('X', None),
])
def test_to_bool_true_value(test_input, expected):
    assert to_bool(0, 'Y', 'N')([test_input]) == expected


@pytest.mark.parametrize('test_input,expected', [
    ('0', True),
    ('1', True),
    ('2', False),
    ('3', False),
])
def test_dnb_indicator_to_bool(test_input, expected):
    assert dnb_indicator_to_bool(0)([test_input]) == expected


class TestCompanyResource:

    def test_extract(self):

        resource = CompanyResource(TEST_ROW_DATA)

        assert resource.data['duns_number'] == '123456'
        assert resource.data['country_code'] == 357
        assert resource.data['year_started'] == 2000
        assert not resource.data['is_employees_number_estimated']
        assert resource.data['is_annual_sales_estimated']

        assert resource.is_valid()

    def test_is_valid_with_missing_duns_number(self):

        data = TEST_ROW_DATA[:]
        data[5] = ''

        resource = CompanyResource(data)

        assert not resource.is_valid()

    @pytest.mark.django_db
    def test_get_or_create(self):
        company, created = CompanyResource(TEST_ROW_DATA).get_or_create()

        assert created
        assert company.last_updated_source == Company.LAST_UPDATED_FILE
        assert company.duns_number == '123456'
