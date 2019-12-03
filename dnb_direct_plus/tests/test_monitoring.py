from collections import OrderedDict
import copy
import datetime
import io
import json

from freezegun import freeze_time
import pytest
from django.utils import timezone

from company.constants import MonitoringStatusChoices
from company.models import Company
from company.serialisers import CompanySerialiser
from company.tests.factories import (
    CompanyFactory,
    PrimaryIndustryCodeFactory,
    IndustryCodeFactory,
    RegistrationNumberFactory,
)
from dnb_direct_plus.monitoring import (
    apply_update_to_company,
    add_companies_to_monitoring_registration,
    DNBApiError,
    process_exception_file,
    update_company_from_source,
    _update_dict_key,
)

pytestmark = [
    pytest.mark.django_db
]


class TestProcessExceptionsFile:
    def test_invalid_header_raises_exception(self, mocker):
        header = io.BytesIO('INVALID\tHEADER\nanother line\netc\n'.encode('utf-8'))

        mocked = mocker.patch('dnb_direct_plus.monitoring.open_zip_file')
        mocked.return_value.__enter__.return_value = header
        mocked.return_value.__exit__.return_value = False

        with pytest.raises(ValueError):
            process_exception_file('dummy_file.zip')

    def test_company_status_is_updated_to_failure(self, mocker):
        duns_number = '12345678'

        company = CompanyFactory(duns_number=duns_number)

        header = io.BytesIO('DUNS\tCode\tInformation\n12345678\t110110\terror\n'.encode('utf-8'))

        mocked = mocker.patch('dnb_direct_plus.monitoring.open_zip_file')
        mocked.return_value.__enter__.return_value = header
        mocked.return_value.__exit__.return_value = False

        process_exception_file('dummy_file.zip')

        company.refresh_from_db()

        assert company.monitoring_status == MonitoringStatusChoices.failed.name
        assert company.monitoring_status_detail == '110110 error'


class TestUpdateCompanyFromSource:
    def test_update_with_unsaved_company(self, cmpelk_api_response_json):
        source_data = json.loads(cmpelk_api_response_json)

        update_company_from_source(Company(), source_data, None, enable_monitoring=False)

        company = Company.objects.first()
        assert Company.objects.count() == 1

        assert CompanySerialiser(company).data == {
            'duns_number': '987654321',
            'global_ultimate_duns_number': '12345679',
            'primary_name': 'Test Company, Inc.',
            'global_ultimate_primary_name': 'Test Company, Inc.',
            'trading_names': [],
            'domain': '',
            'address_line_1': '492 Koller St',
            'address_line_2': '',
            'address_town': 'San Francisco',
            'address_county': 'San Francisco',
            'address_country': 'US',
            'address_postcode': '94110',
            'registered_address_line_1': '',
            'registered_address_line_2': '',
            'registered_address_town': '',
            'registered_address_county': '',
            'registered_address_country': None,
            'registered_address_postcode': '',
            'line_of_business': '',
            'is_out_of_business': False,
            'year_started': None,
            'employee_number': 153,
            'is_employees_number_estimated': False,
            'annual_sales': 22589957.0,
            'annual_sales_currency': 'USD',
            'is_annual_sales_estimated': None,
            'legal_status': 'corporation',
            'registration_numbers': [],
            'primary_industry_codes': [],
            'industry_codes': [
                OrderedDict([
                    ('code', '323111'),
                    ('description', 'Commercial Printing (except Screen and Books)'),
                    ('priority', 1),
                    ('typeDescription', 'North American Industry Classification System 2017'),
                    ('typeDnBCode', '30832')
                ])
            ]
        }

    def test_update_existing_company_success(self, cmpelk_api_response_json):
        company = CompanyFactory()
        IndustryCodeFactory(company=company)
        PrimaryIndustryCodeFactory(company=company)
        RegistrationNumberFactory(company=company)

        source_data = json.loads(cmpelk_api_response_json)

        update_company_from_source(company, source_data, None, enable_monitoring=False)

        assert Company.objects.count() == 1

        assert CompanySerialiser(company).data == {
            'duns_number': '987654321',
            'global_ultimate_duns_number': '12345679',
            'primary_name': 'Test Company, Inc.',
            'global_ultimate_primary_name': 'Test Company, Inc.',
            'trading_names': [],
            'domain': '',
            'address_line_1': '492 Koller St',
            'address_line_2': '',
            'address_town': 'San Francisco',
            'address_county': 'San Francisco',
            'address_country': 'US',
            'address_postcode': '94110',
            'registered_address_line_1': '',
            'registered_address_line_2': '',
            'registered_address_town': '',
            'registered_address_county': '',
            'registered_address_country': None,
            'registered_address_postcode': '',
            'line_of_business': '',
            'is_out_of_business': False,
            'year_started': None,
            'employee_number': 153,
            'is_employees_number_estimated': False,
            'annual_sales': 22589957.0,
            'annual_sales_currency': 'USD',
            'is_annual_sales_estimated': None,
            'legal_status': 'corporation',
            'registration_numbers': [],
            'primary_industry_codes': [],
            'industry_codes': [
                OrderedDict([
                    ('code', '323111'),
                    ('description', 'Commercial Printing (except Screen and Books)'),
                    ('priority', 1),
                    ('typeDescription', 'North American Industry Classification System 2017'),
                    ('typeDnBCode', '30832'),
                ])
            ]
        }

    def test_last_updated_field_not_modified_if_data_unchanged(self, cmpelk_api_response_json):
        """If there are no changes to the model, then the last_updated field should not be changed"""

        with freeze_time('2019-11-25 12:00:01 UTC') as frozen_time:
            source_data = json.loads(cmpelk_api_response_json)

            update_company_from_source(Company(), source_data, None, enable_monitoring=False)

            assert Company.objects.count() == 1
            company = Company.objects.first()
            original_update_time = timezone.now()

            assert original_update_time == company.last_updated

            frozen_time.move_to('2019-11-28 20:00:01 UTC')

            update_company_from_source(company, source_data, None, enable_monitoring=False)

            company.refresh_from_db()

            assert company.last_updated == original_update_time

    def test_update_to_source_data_but_not_model_last_updated_is_not_changed(self, cmpelk_api_response_json):
        with freeze_time('2019-11-25 12:00:01 UTC') as frozen_time:
            source_data = json.loads(cmpelk_api_response_json)

            update_company_from_source(Company(), source_data, None, enable_monitoring=False)

            assert Company.objects.count() == 1
            company = Company.objects.first()
            original_update_time = timezone.now()

            assert original_update_time == company.last_updated

            frozen_time.move_to('2019-11-28 20:00:01 UTC')

            # changing these fields should not result in the last_updated field changing
            source_data['organization']['dunsControlStatus']['isMarketable'] = True
            source_data['organization']['dunsControlStatus']['isDelisted'] = False

            update_company_from_source(company, source_data, None, enable_monitoring=False)

            company.refresh_from_db()

            assert company.last_updated == original_update_time
            assert company.last_updated_source_timestamp is None

    def test_last_updated_field_changed(self, cmpelk_api_response_json):
        """A change to the source API data that results in the company model or associated models being updated
        should result in the last_updated field being changed"""

        with freeze_time('2019-11-25 12:00:01 UTC') as frozen_time:
            source_data = json.loads(cmpelk_api_response_json)

            # changing these fields should not result in the last_updated field changing

            update_company_from_source(Company(), source_data, None, enable_monitoring=False)

            assert Company.objects.count() == 1
            company = Company.objects.first()
            original_update_time = timezone.now()

            assert original_update_time == company.last_updated

            frozen_time.move_to('2019-11-28 20:00:01 UTC')

            new_duns_number = '11111111'

            source_data['organization']['duns'] = new_duns_number
            update_company_from_source(company, source_data, None, enable_monitoring=False)

            company.refresh_from_db()

            assert company.duns_number == new_duns_number
            assert company.last_updated == timezone.now() and timezone.now() != original_update_time
            assert company.last_updated_source_timestamp is None

    @freeze_time('2019-11-25 12:00:01 UTC')
    def test_last_updated_source_timestamp_is_updated(self, cmpelk_api_response_json):
        source_data = json.loads(cmpelk_api_response_json)

        update_company_from_source(Company(), source_data, timezone.now(), enable_monitoring=False)

        company = Company.objects.first()
        assert company.last_updated == timezone.now()
        assert company.last_updated_source_timestamp == timezone.now()

    @pytest.mark.parametrize('status, expected_status',
                             [
                                 (MonitoringStatusChoices.not_enabled.name, MonitoringStatusChoices.pending.name),
                                 (MonitoringStatusChoices.pending.name, MonitoringStatusChoices.pending.name),
                                 (MonitoringStatusChoices.failed.name, MonitoringStatusChoices.failed.name),
                                 (MonitoringStatusChoices.enabled.name, MonitoringStatusChoices.enabled.name),
                             ]
                             )
    @freeze_time('2019-11-25 12:00:01 UTC')
    def test_monitoring_status_changed(self, status, expected_status, cmpelk_api_response_json):
        source_data = json.loads(cmpelk_api_response_json)

        company = CompanyFactory(monitoring_status=status)

        update_company_from_source(company, source_data, timezone.now(), enable_monitoring=True)

        company.refresh_from_db()

        assert company.monitoring_status == expected_status


class TestAddCompaniesToMonitoringRegistration:
    def test_non_202_response_leaves_companies_in_pending_state(self, mocker):
        company = CompanyFactory(monitoring_status=MonitoringStatusChoices.pending.name)

        mocked = mocker.patch('dnb_direct_plus.monitoring.api_request')
        mocked.return_value.json.return_value = {'error': 'an unknown error occured'}
        mocked.return_value.status_code = 500

        with pytest.raises(DNBApiError):
            add_companies_to_monitoring_registration()

        company.refresh_from_db()

        assert company.monitoring_status == MonitoringStatusChoices.pending.name

    def test_company_status_set_to_submitted_on_success(self, mocker):
        company = CompanyFactory(monitoring_status=MonitoringStatusChoices.pending.name)

        mocked = mocker.patch('dnb_direct_plus.monitoring.api_request')
        mocked.return_value.status_code = 202

        add_companies_to_monitoring_registration()

        company.refresh_from_db()

        assert company.monitoring_status == MonitoringStatusChoices.enabled.name


class TestApplyUpdateToCompany:
    @freeze_time('2019-11-25 12:00:01 UTC')
    def test_seed_type_success(self, cmpelk_api_response_json):
        company_data = json.loads(cmpelk_api_response_json)

        company = CompanyFactory(duns_number=company_data['organization']['duns'])

        apply_update_to_company(company_data, timezone.now() + datetime.timedelta(1))

        company.refresh_from_db()

        assert CompanySerialiser(company).data == {
            'duns_number': '987654321',
            'global_ultimate_duns_number': '12345679',
            'primary_name': 'Test Company, Inc.',
            'global_ultimate_primary_name': 'Test Company, Inc.',
            'trading_names': [],
            'domain': '',
            'address_line_1': '492 Koller St',
            'address_line_2': '',
            'address_town': 'San Francisco',
            'address_county': 'San Francisco',
            'address_country': 'US',
            'address_postcode': '94110',
            'registered_address_line_1': '',
            'registered_address_line_2': '',
            'registered_address_town': '',
            'registered_address_county': '',
            'registered_address_country': None,
            'registered_address_postcode': '',
            'line_of_business': '',
            'is_out_of_business': False,
            'year_started': None,
            'employee_number': 153,
            'is_employees_number_estimated': False,
            'annual_sales': 22589957.0,
            'annual_sales_currency': 'USD',
            'is_annual_sales_estimated': None,
            'legal_status': 'corporation',
            'registration_numbers': [],
            'primary_industry_codes': [],
            'industry_codes': [
                OrderedDict([
                    ('code', '323111'),
                    ('description', 'Commercial Printing (except Screen and Books)'),
                    ('priority', 1),
                    ('typeDescription', 'North American Industry Classification System 2017'),
                    ('typeDnBCode', '30832'),
                ])
            ]
        }

    def test_update_type_success(self, cmpelk_api_response_json):
        company_data = json.loads(cmpelk_api_response_json)

        update_company_from_source(Company(), company_data, None, enable_monitoring=False)

        assert Company.objects.count() == 1
        company = Company.objects.first()

        assert company.primary_name == 'Test Company, Inc.'

        update_data = {
            'type': 'UPDATE',
            'organization': {
                'duns': company_data['organization']['duns']
            },
            'elements': [
                {
                    'element': 'organization.primaryName',
                    'previous': '',
                    'current': 'Acme Corp',
                    'timestamp': '2019-06-25T01:00:17Z"'
                },
                {
                    'element': 'organization.corporateLinkage.globalUltimate.primaryName',
                    'previous': '',
                    'current': 'Acme Corp HQ',
                    'timestamp': '2019-06-25T01:00:17Z"'
                },
                {
                    'element': 'organization.tradeStyleNames',
                    'previous': '',
                    'current': [{'name': 'Acme enterprises'}, {'name': 'Acme heavy industries'}],
                    'timestamp': '2019-06-25T01:00:17Z"'
                },
            ]
        }

        apply_update_to_company(update_data, timezone.now() + datetime.timedelta(1))

        company.refresh_from_db()

        assert CompanySerialiser(company).data == {
            'duns_number': '987654321',
            'global_ultimate_duns_number': '12345679',
            'primary_name': 'Acme Corp',
            'global_ultimate_primary_name': 'Acme Corp HQ',
            'trading_names': ['Acme enterprises', 'Acme heavy industries'],
            'domain': '',
            'address_line_1': '492 Koller St',
            'address_line_2': '',
            'address_town': 'San Francisco',
            'address_county': 'San Francisco',
            'address_country': 'US',
            'address_postcode': '94110',
            'registered_address_line_1': '',
            'registered_address_line_2': '',
            'registered_address_town': '',
            'registered_address_county': '',
            'registered_address_country': None,
            'registered_address_postcode': '',
            'line_of_business': '',
            'is_out_of_business': False,
            'year_started': None,
            'employee_number': 153,
            'is_employees_number_estimated': False,
            'annual_sales': 22589957.0,
            'annual_sales_currency': 'USD',
            'is_annual_sales_estimated': None,
            'legal_status': 'corporation',
            'registration_numbers': [],
            'primary_industry_codes': [],
            'industry_codes': [
                OrderedDict([
                    ('code', '323111'),
                    ('description', 'Commercial Printing (except Screen and Books)'),
                    ('priority', 1),
                    ('typeDescription', 'North American Industry Classification System 2017'),
                    ('typeDnBCode', '30832'),
                ])
            ]
        }

    def test_missing_company_on_update_fails(self):
        company_data = {
            'type': 'UPDATE',
            'organization': {
                'duns': '12345678'
            }
        }

        status, detail = apply_update_to_company(company_data, None)

        assert not status
        assert detail == '12345678: update for company not in DB'

    def test_missing_company_with_seed_creates_new_company(self, cmpelk_api_response_json):

        api_data = json.loads(cmpelk_api_response_json)

        assert Company.objects.count() == 0

        status, detail = apply_update_to_company(api_data, None)

        assert status
        assert Company.objects.count() == 1

    @freeze_time('2019-11-25 12:00:01 UTC')
    def test_old_update(self):
        company_data = {
            'organization': {
                'duns': '12345678'
            }
        }

        CompanyFactory(duns_number=company_data['organization']['duns'], last_updated_source_timestamp=timezone.now())

        status, detail = apply_update_to_company(company_data, timezone.now() - datetime.timedelta(1))

        assert not status
        assert detail == '12345678; update is older than last updated timestamp'

    def test_update_type_missing_source(self):
        company_data = {
            'organization': {
                'duns': '12345678'
            },
            'type': 'UPDATE',
        }

        CompanyFactory(duns_number=company_data['organization']['duns'], source=None)

        status, detail = apply_update_to_company(company_data, timezone.now() - datetime.timedelta(1))

        assert not status
        assert detail == '12345678: No source data - cannot apply update'

    def test_update_type_bad_data(self, cmpelk_api_response_json):
        company_data = json.loads(cmpelk_api_response_json)

        update_company_from_source(Company(), company_data, None, enable_monitoring=False)

        duns_number = company_data['organization']['duns']

        update_data = {
            'organization': {
                'duns': duns_number,
            },
            'type': 'UPDATE',
            "elements": [
                {
                    "element": "a.key.that.was.added",
                    "previous": "n/a", "current": True, "timestamp": "2018-02-20T05:16:20Z"
                },
            ]
        }

        status, detail = apply_update_to_company(
            update_data, timezone.now() - datetime.timedelta(1))

        assert Company.objects.count() == 1
        company = Company.objects.first()
        assert status
        assert company.source['a']['key']['that']['was']['added']


class TestProcessNotificationFile:
    def test_incomplete_line(self):
        pass

    def test_update(self):
        pass

    def test_seed(self):
        pass

    def test_multiple_entries(self):
        pass


class TestUpdateDictKey:
    def test_success(self):

        source = {
            'a': {
                'b': {
                    'c': {
                        'd': {
                            'e': 'test'
                        }
                    }
                }
            }
        }

        expected = copy.deepcopy(source)

        expected['a']['b']['c']['d']['e'] = 'modified'

        assert _update_dict_key(source, 'a.b.c.d.e'.split('.'), 'modified') == expected

    def test_new_element_is_appended(self):
        source = {
            'a': {
                'b': {
                    'c': {
                        'd': {
                            'e': 'test'
                        }
                    }
                }
            }
        }

        expected = copy.deepcopy(source)

        expected['a']['b']['c']['d']['e_sibling'] = 'added'

        assert _update_dict_key(source, 'a.b.c.d.e_sibling'.split('.'), 'added') == expected
