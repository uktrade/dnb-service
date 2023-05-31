import datetime
import json

import pytest
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from requests.exceptions import HTTPError
from rest_framework import status
from rest_framework.test import APITestCase

from company.constants import MonitoringStatusChoices
from company.models import ChangeRequest, Company
from company.serialisers import CompanySerialiser
from company.tests.factories import ChangeRequestFactory, CompanyFactory
from dnb_direct_plus.mapping import extract_company_data

pytestmark = pytest.mark.django_db

class TestSwagger(APITestCase):

    def test_get(self):
        response = self.client.get(
            '/api/swagger/?format=openapi',
            follow=True
        )
        self.assertEquals(response.status_code, 200)


class TestCompanySearchView:
    def test_requires_authentication(self, client):
        response = client.get(reverse('api:company-search'))
        assert response.status_code == 401

    def test_404_returns_empty_data(self, auth_client, mocker):
        mock_api_request = mocker.patch('dnb_direct_plus.api.api_request')
        mock_api_request.side_effect = HTTPError(response=mocker.Mock(status_code=404))

        response = auth_client.post(
            reverse('api:company-search'),
            {'search_term': 'micro'},
        )

        assert response.status_code == 200
        assert response.json() == {
            'total_matches': 0,
            'total_returned': 0,
            'page_size': 0,
            'page_number': 1,
            'results': []
        }

    def test_api_call_with_data(self, auth_client, mocker, company_list_api_response_json):
        company_input_data = json.loads(company_list_api_response_json)

        mock_api_request = mocker.patch('dnb_direct_plus.api.api_request')
        mock_api_request.return_value.json.return_value = company_input_data

        response = auth_client.post(
            reverse('api:company-search'),
            {'search_term': 'micro'},
        )

        assert response.status_code == 200

        response_data = response.json()
        assert response_data['total_matches'] == 2
        assert response_data['total_returned'] == 2
        assert response_data['page_size'] == 0
        assert response_data['page_number'] == 1

        for input_data, expected in zip(company_input_data['searchCandidates'], response_data['results']):
            assert extract_company_data(input_data) == expected

    def test_api_with_bad_query(self, auth_client):
        response = auth_client.post(
            reverse('api:company-search'),
            {},
        )

        assert response.status_code == 400

        expected_response = {
            'non_field_errors': [
                "At least one standalone field required: ['duns_number', 'search_term', 'primary_name', "
                "'registration_numbers']."
            ]
        }
        assert response.json() == expected_response

    def test_api_with_empty_registration_numbers(self, auth_client):
        response = auth_client.post(
            reverse('api:company-search'),
            {'registration_numbers': []}
        )

        assert response.status_code == 400

        expected_response = {
            'registration_numbers': ["Ensure this field has at least 1 elements."]
        }
        assert response.json() == expected_response

    def test_query_duns_number_updates_local_db_and_monitoring_is_enabled(
        self,
        auth_client,
        mocker,
        company_list_api_response_json,
    ):

        company_input_data = json.loads(company_list_api_response_json)
        company_input_data['searchCandidates'].pop()
        company_input_data['candidatesReturnedQuantity'] = 1
        company_input_data['candidatesMatchedQuantity'] = 1

        mock_api_request = mocker.patch('dnb_direct_plus.api.api_request')
        mock_api_request.return_value.json.return_value = company_input_data

        assert Company.objects.count() == 0
        response = auth_client.post(
            reverse('api:company-search'),
            {'duns_number': company_input_data['searchCandidates'][0]['organization']['duns']},
        )

        assert Company.objects.count() == 1
        assert response.status_code == 200
        company = Company.objects.first()
        result_data = response.json()
        assert company.duns_number == result_data['results'][0]['duns_number']
        assert company.monitoring_status == MonitoringStatusChoices.pending.name


class TestCompanySearchV2View:
    def test_requires_authentication(self, client):
        response = client.get(reverse('api:company-search-v2'))

        assert response.status_code == 401

    def test_404_returns_empty_data(self, auth_client, mocker):
        mock_api_request = mocker.patch('dnb_direct_plus.api.api_request')
        mock_api_request.side_effect = HTTPError(response=mocker.Mock(status_code=404))

        response = auth_client.post(
            reverse('api:company-search-v2'),
            {'search_term': 'micro'},
        )

        assert response.status_code == 200
        assert response.json() == {
            'results': []
        }

    def test_api_call_with_data(self, auth_client, mocker, company_list_v2_api_response_json, company_list_v2_expected_data_json):
        company_input_data = json.loads(company_list_v2_api_response_json)
        expected_company_data = json.loads(company_list_v2_expected_data_json)

        mock_api_request = mocker.patch('dnb_direct_plus.api.api_request')
        mock_api_request.return_value.json.return_value = company_input_data

        response = auth_client.post(
            reverse('api:company-search-v2'),
            {'search_term': 'micro'},
        )

        assert response.status_code == 200

        response_data = response.json()

        for expected_data, result_data in zip(expected_company_data, response_data['results']):
            assert extract_company_data(expected_data) == result_data

    def test_api_with_bad_query(self, auth_client):
        response = auth_client.post(
            reverse('api:company-search-v2'),
            {},
        )

        assert response.status_code == 400

        expected_response = {
            'non_field_errors': [
                "At least one standalone field required: ['duns_number', 'search_term']."
            ]
        }
        assert response.json() == expected_response

    def test_query_duns_number_updates_local_db_and_monitoring_is_enabled(
        self,
        auth_client,
        mocker,
        company_list_v2_api_response_json,
        data_duns_api_response_json
    ):

        company_input_data = json.loads(company_list_v2_api_response_json)
        up_to_date_company_data = json.loads(data_duns_api_response_json)

        class ApiRequestFake:
            def __init__(self, *posargs, **kwargs):
                self.posargs = posargs
                self.kwargs = kwargs

                if self.posargs == ('GET', '/v1/match/cleanseMatch'):
                    assert self.kwargs['params'] == {
                        'duns': '141592653'
                    }

                    self.json_data = company_input_data
                elif self.posargs == ('GET', '/v1/data/duns/141592653'):
                    self.json_data = up_to_date_company_data
                else:
                    raise AssertionError(f'Unexpected API request posargs={posargs} kwargs={kwargs}')

            def json(self):
                return self.json_data

        mock_api_request = mocker.patch('dnb_direct_plus.api.api_request', new=ApiRequestFake)

        assert Company.objects.count() == 0
        response = auth_client.post(
            reverse('api:company-search-v2'),
            {'duns_number': company_input_data['matchCandidates'][0]['organization']['duns']},
        )

        assert Company.objects.count() == 1
        assert response.status_code == 200
        company = Company.objects.first()
        result_data = response.json()

        assert company.address_country.iso_alpha2 == up_to_date_company_data['organization']['primaryAddress']['addressCountry']['isoAlpha2Code']
        assert company.duns_number == result_data['results'][0]['duns_number']
        assert company.monitoring_status == MonitoringStatusChoices.pending.name


class TestCompanyUpdateView:
    def _iso_now(self):
        return datetime.datetime.isoformat(datetime.datetime.now(), sep='T')

    def test_requires_authentication(self, client):
        response = client.get(reverse('api:company-updates'))

        assert response.status_code == 401

    @freeze_time('2019-11-25 12:00:01 UTC')
    def test_last_updated_field(self, auth_client):
        CompanyFactory(last_updated=timezone.now() - datetime.timedelta(1), source={'not_empty': True})
        company = CompanyFactory(last_updated=timezone.now() + datetime.timedelta(1), source={'not_empty': True})

        expected_company_data = CompanySerialiser(company).data

        response = auth_client.get(
            reverse('api:company-updates'),
            {'last_updated_after': self._iso_now()},
        )

        assert response.status_code == 200
        assert response.json() == {
            'next': None,
            'previous': None,
            'results': [
                expected_company_data
            ],
        }

    def test_last_updated_invalid_date_results_in_400(self, auth_client):
        response = auth_client.get(
            reverse('api:company-updates'),
            {'last_updated_after': 'is-not-a-date'},
        )

        assert response.status_code == 400
        assert response.json() == {'detail': 'Invalid date: is-not-a-date'}


    def test_no_params_returns_all_results(self, auth_client):
        duns_numbers = [
            CompanyFactory(source={'not_empty': True}).duns_number,
            CompanyFactory(source={'not_empty': True}).duns_number
        ]

        response = auth_client.get(
            reverse('api:company-updates'),
            {},
        )

        assert response.status_code == 200

        result_data = response.json()
        assert len(result_data['results']) == 2
        assert all(result['duns_number'] in duns_numbers for result in result_data['results'])

    @freeze_time('2019-11-25 12:00:01 UTC')

    def test_pagination(self, auth_client):
        company1 = CompanyFactory(last_updated=timezone.now() + datetime.timedelta(1), source={'not_empty': True})
        company2 = CompanyFactory(last_updated=timezone.now() + datetime.timedelta(2), source={'not_empty': True})

        response = auth_client.get(
            reverse('api:company-updates'),
            {'last_updated_after': self._iso_now(), 'page_size': 1},
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data['next'] is not None
        assert len(response_data['results']) == 1
        assert response_data['results'][0]['duns_number'] == company1.duns_number

        response = auth_client.get(
            response_data['next'],
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data['next'] is None
        assert len(response_data['results']) == 1
        assert response_data['results'][0]['duns_number'] == company2.duns_number

    def test_source_field_is_required(self, auth_client):

        CompanyFactory(last_updated=timezone.now() - datetime.timedelta(1), source=None)

        response = auth_client.get(
            reverse('api:company-updates'),
            content_type='application/json'
        )

        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data['results']) == 0


class TestCompanyHierarchySearchView:
    
    def test_hierachy_requires_authentication(self, client):
        response = client.get(reverse('api:company-hierarchy-search'))
        assert response.status_code == 401


    def test_404_returns_empty_data(self, auth_client, mocker):
        mock_api_request = mocker.patch('dnb_direct_plus.api.api_request')
        mock_api_request.side_effect = HTTPError(response=mocker.Mock(status_code=404))

        response = auth_client.post(
            reverse('api:company-hierarchy-search'),
            {'duns_number': '000000000'},
        )

        assert response.status_code == 200
        assert response.json() == {"family_tree_members": []}

    def test_api_call_with_data(self, auth_client, mocker, company_hierarchy_api_response_json):
        company_hierarchy_data = json.loads(company_hierarchy_api_response_json)

        mock_api_request = mocker.patch('dnb_direct_plus.api.api_request')
        mock_api_request.return_value.json.return_value = company_hierarchy_data

        response = auth_client.post(
            reverse('api:company-hierarchy-search'),
            {'duns_number': '111111111'},
        )
        
        assert response.status_code == 200

        response_data = response.json()

        assert response_data['global_ultimate_duns'] == '111111111'
        assert response_data['global_ultimate_family_tree_members_count'] == 3
        assert response_data['branches_excluded_members_count'] == 2
        assert response_data['family_tree_members'][0]['duns'] == '111111111'
        assert response_data['family_tree_members'][1]['duns'] == '222222222'
        assert response_data['family_tree_members'][2]['duns'] == '333333333'

    def test_api_with_bad_query(self, auth_client):
        response = auth_client.post(
            reverse('api:company-hierarchy-search'),
            {},
        )

        assert response.status_code == 400

        expected_response = {
            'non_field_errors': [
                "At least one standalone field required: ['duns_number']."
            ]
        }
        assert response.json() == expected_response

    def test_api_with_invalid_duns_number(self, auth_client):
        response = auth_client.post(
            reverse('api:company-hierarchy-search'),
            {'duns_number': '12345678'}
        )

        assert response.status_code == 400

        expected_response = {
            "duns_number": ["This value does not match the required pattern."]
        }
        assert response.json() == expected_response

class TestChangeRequestApiView:
    """
    Test the change-request API endpoint.
    """

    def test_requires_authentication(self, client):
        """
        Test that requests without authentication are not permitted.
        """
        response = client.post(reverse('api:change-request'))

        assert response.status_code == 401

    @pytest.mark.parametrize(
        'request_data,expected_error_message',
        (
            (
                {
                    "duns_number": "1",
                },
                {
                    'duns_number': ['Field should contain 9 numbers only'],
                    'changes': ['This field is required.'],
                },
            ),
            (
                {
                    "duns_number": "123456789",
                    "changes": {
                        "annual_sales": "foooooooob",
                    },
                },
                {'changes': {'annual_sales': ['A valid number is required.']}},
            ),
            (
                {
                    "duns_number": "123456789",
                    "changes": {
                        "address_country": "99",
                    },
                },
                {'changes': {'address_country': ['This is not a valid ISO Alpha2 country code.']}},
            ),
            (
                {
                    "duns_number": "123456789",
                    "changes": {
                        "address_line_1": "Foo",
                    },
                },
                {
                    'changes': {
                        'non_field_errors': [
                            "If any 'address' fields are set, all 'address' fields must be set."
                        ]
                    }
                },
            ),
        )
    )
    def test_invalid_request_responds_400(self, auth_client, request_data, expected_error_message):
        """
        Test that various badly formed inputs are rejected with 400 responses.
        """
        response = auth_client.post(
            reverse('api:change-request'),
            request_data,
        )
        assert response.status_code == 400
        assert response.json() == expected_error_message

    @freeze_time('2019-11-25 12:00:01 UTC')
    @pytest.mark.parametrize(
        'request_data',
        (
            {
                'duns_number': '123456789',
                'changes': {
                    'primary_name': 'Foo Bar',
                    'trading_names': ['Foo Bar INC'],
                    'domain': 'example.com',
                    'address_line_1': '123 Fake Street',
                    'address_line_2': 'Foo',
                    'address_town': 'London',
                    'address_county': 'Greater London',
                    'address_country': 'GB',
                    'address_postcode': 'W1 0TN',
                    'registered_address_line_1': '123 Fake Street',
                    'registered_address_line_2': '',
                    'registered_address_town': 'London',
                    'registered_address_county': 'Greater London',
                    'registered_address_country': 'GB',
                    'registered_address_postcode': 'W1 0TN',
                    'employee_number': 673,
                    'annual_sales': 416807212.0,
                    'annual_sales_currency': 'GBP',
                },
            },
            # No registered address fields
            {
                'duns_number': '123456789',
                'changes': {
                    'primary_name': 'Foo Bar',
                    'trading_names': ['Foo Bar INC'],
                    'domain': 'example.com',
                    'address_line_1': '123 Fake Street',
                    'address_line_2': 'Foo',
                    'address_town': 'London',
                    'address_county': 'Greater London',
                    'address_country': 'GB',
                    'address_postcode': 'W1 0TN',
                    'employee_number': 673,
                    'annual_sales': 416807212.0,
                    'annual_sales_currency': 'GBP',
                },
            },
            # No address fields
            {
                'duns_number': '123456789',
                'changes': {
                    'primary_name': 'Foo Bar',
                    'trading_names': ['Foo Bar INC'],
                    'domain': 'example.com',
                    'employee_number': 673,
                    'annual_sales': 416807212.0,
                    'annual_sales_currency': 'GBP',
                },
            },
            # Only address fields
            {
                'duns_number': '123456789',
                'changes': {
                    'address_line_1': '123 Fake Street',
                    'address_line_2': 'Foo',
                    'address_town': 'London',
                    'address_county': 'Greater London',
                    'address_country': 'GB',
                    'address_postcode': 'W1 0TN',
                },
            },
            # US Company
            {
                'duns_number': '123456789',
                'changes': {
                    'primary_name': 'Foo Bar',
                    'trading_names': ['Foo Bar INC'],
                    'domain': 'example.com',
                    'address_line_1': '123 Fake Street',
                    'address_line_2': 'Foo',
                    'address_town': 'Beverly Hills',
                    'address_county': 'Los Angeles',
                    'address_area': {'name': 'California', 'abbrev_name': 'CA'},
                    'address_country': 'US',
                    'address_postcode': '90210',
                    'registered_address_line_1': '123 Fake Street',
                    'registered_address_line_2': 'Foo',
                    'registered_address_town': 'Beverly Hills',
                    'registered_address_county': 'Los Angeles',
                    'registered_address_area': {'name': 'California', 'abbrev_name': 'CA'},
                    'registered_address_country': 'US',
                    'registered_address_postcode': '90210',
                    'employee_number': 673,
                    'annual_sales': 416807212.0,
                    'annual_sales_currency': 'USD',
                },
            },
        )
    )
    def test_valid_request_responds_200(self, auth_client, request_data):
        """
        Test that a valid request responds with a 200.
        """
        response = auth_client.post(
            reverse('api:change-request'),
            request_data,
        )
        assert response.status_code == 201
        assert ChangeRequest.objects.all().count() == 1
        change_request = ChangeRequest.objects.first()

        # Assert that the response is correctly formatted
        response_data = response.json()
        expected_response_data = {
            'id': str(change_request.id),
            'status': 'pending',
            'created_on': '2019-11-25T12:00:01Z',
            **request_data,
        }
        assert response_data == expected_response_data

        # Assert that the ChangeRequest has been saved correctly in the DB
        assert change_request.status == 'pending'
        assert change_request.created_on == timezone.now()
        assert change_request.duns_number == request_data['duns_number']
        assert change_request.changes == request_data['changes']

    @freeze_time('2020-05-18 12:00:01 UTC')
    def test_no_params_returns_all_results(self, auth_client):
        """
        Test that all change requests return if no filter parameters are specified.
        """
        duns_numbers = [
            ChangeRequestFactory(
                changes={'primary_name': 'bar'},
                status='pending',
                id='00000000-0000-0000-0000-000000000001'
                ).duns_number,
            ChangeRequestFactory(
                changes={'primary_name': 'baz'},
                status='submitted',
                id='00000000-0000-0000-0000-000000000002'
                ).duns_number
            ]

        response = auth_client.get(
            reverse('api:change-request'),
            {},
        )

        assert response.status_code == 200

        result_data = response.json()
        assert result_data['count'] == 2

        expected_result_data = {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'id': '00000000-0000-0000-0000-000000000001',
                    'duns_number': '000000000',
                    'changes': {'primary_name': 'bar'},
                    'status': 'pending',
                    'created_on': '2020-05-18T12:00:01Z'
                },
                {
                    'id': '00000000-0000-0000-0000-000000000002',
                    'duns_number': '000000001',
                    'changes': {'primary_name': 'baz'},
                    'status': 'submitted',
                    'created_on': '2020-05-18T12:00:01Z'
                }
            ]
        }

        assert result_data == expected_result_data

    @freeze_time('2020-05-18 12:00:01 UTC')
    def test_only_returns_pending_requests(self, auth_client):
        """
        Test that all pending change requests can be returned, for any company.
        """
        pending_duns_numbers = [
            ChangeRequestFactory(changes={'primary_name': 'test1'}, status='pending', id='00000000-0000-0000-0000-000000000001'),
            ChangeRequestFactory(changes={'primary_name': 'test2'}, status='pending', id='00000000-0000-0000-0000-000000000002'),
        ]

        ChangeRequestFactory(changes={'primary_name': 'test3'}, status='submitted')
        ChangeRequestFactory(changes={'primary_name': 'test4'}, status='submitted')


        response = auth_client.get(
            reverse('api:change-request'),
            {'status': 'pending'},
        )

        assert response.status_code == 200

        result_data = response.json()
        assert result_data['count'] == 2

        expected_result_data = {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'id': '00000000-0000-0000-0000-000000000002',
                    'duns_number': '000000003',
                    'changes': {'primary_name': 'test2'},
                    'status': 'pending',
                    'created_on': '2020-05-18T12:00:01Z'
                },
                {
                    'id': '00000000-0000-0000-0000-000000000001',
                    'duns_number': '000000002',
                    'changes': {'primary_name': 'test1'},
                    'status': 'pending',
                    'created_on': '2020-05-18T12:00:01Z'
                }

            ]
        }

        assert result_data == expected_result_data

    def test_only_returns_submitted_requests(self, auth_client):
        """
        Test that all submitted change requests can be returned, for any company.
        """
        submitted_duns_numbers = [
            ChangeRequestFactory(changes={'primary_name': 'test1'}, status='submitted'),
            ChangeRequestFactory(changes={'primary_name': 'test2'}, status='submitted'),
        ]

        ChangeRequestFactory(changes={'primary_name': 'test3'}, status='pending')
        ChangeRequestFactory(changes={'primary_name': 'test4'}, status='pending')


        response = auth_client.get(
            reverse('api:change-request'),
            {'status': 'submitted'},
        )

        assert response.status_code == 200

        result_data = response.json()
        assert len(result_data['results']) == 2
        assert result_data['count'] == 2

    def test_only_returns_pending_requests_with_specific_duns_number(self, auth_client):
        """
        Test that all pending change requests are returned for a specific company.
        """
        change_requests = [
            ChangeRequestFactory(changes={'primary_name': 'test1'}, status='pending', duns_number='123456789', id='00000000-0000-0000-0000-000000000001'),
            ChangeRequestFactory(changes={'primary_name': 'test2'}, status='pending', duns_number='123456789', id='00000000-0000-0000-0000-000000000002'),
            ChangeRequestFactory(changes={'primary_name': 'test3'}, status='pending', duns_number='123056789', id='00000000-0000-0000-0000-000000000003'),
            ChangeRequestFactory(changes={'primary_name': 'test4'}, status='pending', duns_number='123406780', id='00000000-0000-0000-0000-000000000004'),
        ]

        test_ids = []

        for request in change_requests:
            if request.duns_number == '123456789':
                test_ids.append(request.id)

        response = auth_client.get(
            reverse('api:change-request'),
            {'status': 'pending', 'duns_number': '123456789'},
        )

        assert response.status_code == 200

        result_data = response.json()

        assert len(result_data['results']) == 2
        assert result_data['count'] == 2

        for result in result_data['results']:
            assert result['id'] in test_ids

    def test_only_duns_param_returns_all_results(self, auth_client):
        """
        Test that all change requests for a company can be returned.
        """
        change_requests = [
            ChangeRequestFactory(changes={'primary_name': 'test1'}, duns_number='123456789', id='00000000-0000-0000-0000-000000000001'),
            ChangeRequestFactory(changes={'primary_name': 'test2'}, duns_number='123456789', id='00000000-0000-0000-0000-000000000002'),
            ChangeRequestFactory(changes={'primary_name': 'test3'}, duns_number='123456789', id='00000000-0000-0000-0000-000000000003'),
            ChangeRequestFactory(changes={'primary_name': 'test4'}, duns_number='123456700', id='00000000-0000-0000-0000-000000000004'),
        ]

        test_ids = []

        for request in change_requests:
            if request.duns_number == '123456789':
                test_ids.append(request.id)

        response = auth_client.get(
            reverse('api:change-request'),
            {'duns_number': '123456789'},
        )

        assert response.status_code == 200

        result_data = response.json()

        assert len(result_data['results']) == 3
        assert result_data['count'] == 3

        for result in result_data['results']:
            assert result['id'] in test_ids

class TestInvestigationApiView:
    """
    Test the investigation API endpoint.
    """

    def test_requires_authentication(self, client):
        """
        Test that requests without authentication are not permitted.
        """
        response = client.post(
            reverse('api:investigation')
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @freeze_time('2019-11-25 12:00:01 UTC')
    @pytest.mark.parametrize(
        'request_data',
        (
            {
                'company_details': {
                    'primary_name': 'Foo Bar',
                    'domain': 'example.com',
                    'telephone_number': '12345678',
                    'address_line_1': '123 Fake Street',
                    'address_line_2': 'Foo',
                    'address_town': 'London',
                    'address_county': 'Greater London',
                    'address_country': 'GB',
                    'address_postcode': 'W1 0TN',
                },
            },
            # No domain
            {
                'company_details': {
                    'primary_name': 'Foo Bar',
                    'telephone_number': '12345678',
                    'address_line_1': '123 Fake Street',
                    'address_line_2': 'Foo',
                    'address_town': 'London',
                    'address_county': 'Greater London',
                    'address_country': 'GB',
                    'address_postcode': 'W1 0TN',
                },
            },
            # No telephone_number
            {
                'company_details': {
                    'primary_name': 'Foo Bar',
                    'domain': 'example.com',
                    'address_line_1': '123 Fake Street',
                    'address_line_2': 'Foo',
                    'address_town': 'London',
                    'address_county': 'Greater London',
                    'address_country': 'GB',
                    'address_postcode': 'W1 0TN',
                },
            },
            # No non-required address fields
            {
                'company_details': {
                    'primary_name': 'Foo Bar',
                    'domain': 'example.com',
                    'telephone_number': '12345678',
                    'address_line_1': '123 Fake Street',
                    'address_town': 'London',
                    'address_country': 'GB',
                },
            },
            # US Company
            {
                'company_details': {
                    'primary_name': 'Foo Bar',
                    'domain': 'example.com',
                    'telephone_number': '12345678',
                    'address_line_1': '123 Fake Street',
                    'address_line_2': 'Foo',
                    'address_town': 'Beverly Hills',
                    'address_county': 'Los Angeles',
                    'address_area': {
                        'name': 'California',
                        'abbrev_name': 'CA',
                    },
                    'address_country': 'US',
                    'address_postcode': '90210',
                },
            },
        )
    )
    def test_valid(self, auth_client, request_data):
        """
        Test that a valid investigation payload returns the expected
        response.
        """
        response = auth_client.post(
            reverse('api:investigation'),
            request_data,
        )
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        response_data.pop('id')
        assert response_data == {
            'status': 'pending',
            'created_on': '2019-11-25T12:00:01Z',
            'submitted_on': None,
            **request_data,
        }

    @pytest.mark.parametrize(
        'request_data, expected_response',
        (
            # Missing company_details
            (
                {},
                {
                    'company_details': ['This field is required.'],
                },
            ),
            # Missing primary_name
            (
                {
                    'company_details': {
                        'domain': 'example.com',
                        'telephone_number': '12345678',
                        'address_line_1': '123 Fake Street',
                        'address_line_2': 'Foo',
                        'address_town': 'London',
                        'address_county': 'Greater London',
                        'address_country': 'GB',
                        'address_postcode': 'W1 0TN',
                    },
                },
                {
                    'company_details': {
                        'primary_name': ['This field is required.'],
                    },
                },
            ),
            # Missing domain & telephone_number
            (
                {
                    'company_details': {
                        'primary_name': 'Foo Bar',
                        'address_line_1': '123 Fake Street',
                        'address_line_2': 'Foo',
                        'address_town': 'London',
                        'address_county': 'Greater London',
                        'address_country': 'GB',
                        'address_postcode': 'W1 0TN',
                    },
                },
                {
                    'company_details': {
                        'non_field_errors': [
                            'Either domain or telephone_number must be '
                            'provided for D&B investigation.'
                        ],
                    },
                },
            ),
            # Missing address_line_1
            (
                {
                    'company_details': {
                        'primary_name': 'Foo Bar',
                        'domain': 'example.com',
                        'address_line_2': 'Foo',
                        'address_town': 'London',
                        'address_county': 'Greater London',
                        'address_country': 'GB',
                        'address_postcode': 'W1 0TN',
                    },
                },
                {
                    'company_details': {
                        'address_line_1': ['This field is required.'],
                    },
                },
            ),
            # Missing address_town
            (
                {
                    'company_details': {
                        'primary_name': 'Foo Bar',
                        'domain': 'example.com',
                        'address_line_1': '123 Fake Street',
                        'address_line_2': 'Foo',
                        'address_county': 'Greater London',
                        'address_country': 'GB',
                        'address_postcode': 'W1 0TN',
                    },
                },
                {
                    'company_details': {
                        'address_town': ['This field is required.'],
                    },
                },
            ),
            # Missing address_country
            (
                {
                    'company_details': {
                        'primary_name': 'Foo Bar',
                        'domain': 'example.com',
                        'address_line_1': '123 Fake Street',
                        'address_line_2': 'Foo',
                        'address_town': 'London',
                        'address_county': 'Greater London',
                        'address_postcode': 'W1 0TN',
                    },
                },
                {
                    'company_details': {
                        'address_country': ['This field is required.'],
                    },
                },
            ),
            # Invalid address_country
            (
                {
                    'company_details': {
                        'primary_name': 'Foo Bar',
                        'domain': 'example.com',
                        'address_line_1': '123 Fake Street',
                        'address_line_2': 'Foo',
                        'address_town': 'London',
                        'address_county': 'Greater London',
                        'address_country': 'XX',
                        'address_postcode': 'W1 0TN',
                    },
                },
                {
                    'company_details': {
                        'address_country': ['This is not a valid ISO Alpha2 country code.'],
                    },
                },
            ),
        )
    )
    def test_invalid(self, auth_client, request_data, expected_response):
        """
        Test that an invalid investigation payload returns a 400 response and
        a helpful error message.
        """
        response = auth_client.post(
            reverse('api:investigation'),
            request_data,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_response
