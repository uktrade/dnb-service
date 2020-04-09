import datetime
import json

import pytest

from django.contrib.auth import get_user_model

from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from requests.exceptions import HTTPError
from rest_framework import status
from rest_framework.authtoken.models import Token

from company.constants import MonitoringStatusChoices
from company.models import ChangeRequest, Company
from company.serialisers import CompanySerialiser
from company.tests.factories import CompanyFactory
from dnb_direct_plus.mapping import extract_company_data


pytestmark = pytest.mark.django_db


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
            'non_field_errors': ["At least one standalone field required: ['duns_number', 'search_term']."]
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
            'count': 1,
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
        assert result_data['count'] == 2
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
        assert response_data['count'] == 2
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
