import datetime
import json

import pytest
from freezegun import freeze_time
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from company.constants import MonitoringStatusChoices
from company.models import Company
from company.serialisers import CompanySerialiser
from company.tests.factories import CompanyFactory
from dnb_direct_plus.mapping import extract_company_data
from requests.exceptions import HTTPError
from rest_framework.authtoken.models import Token


pytestmark = [
    pytest.mark.django_db
]


class TestCompanySearchView:
    def test_requires_authentication(self, client):
        response = client.get(reverse('api:company-search'))

        assert response.status_code == 401

    def test_404_returns_empty_data(self, client, mocker):
        user = get_user_model().objects.create(email='test@test.com', is_active=True)
        token = Token.objects.create(user=user)

        mock_api_request = mocker.patch('dnb_direct_plus.api.api_request')
        mock_api_request.side_effect = HTTPError(response=mocker.Mock(status_code=404))

        response = client.post(reverse('api:company-search'),
                               {'search_term': 'micro'},
                               content_type='application/json',
                               HTTP_AUTHORIZATION=f'Token {token.key}')

        assert response.status_code == 200
        assert response.json() == {
            'total_matches': 0,
            'total_returned': 0,
            'page_size': 0,
            'page_number': 1,
            'results': []
        }

    def test_api_call_with_data(self, client, mocker, company_list_api_response_json):
        user = get_user_model().objects.create(email='test@test.com', is_active=True)
        token = Token.objects.create(user=user)

        company_input_data = json.loads(company_list_api_response_json)

        mock_api_request = mocker.patch('dnb_direct_plus.api.api_request')
        mock_api_request.return_value.json.return_value = company_input_data

        response = client.post(reverse('api:company-search'),
                               {'search_term': 'micro'},
                               content_type='application/json',
                               HTTP_AUTHORIZATION=f'Token {token.key}')

        assert response.status_code == 200

        response_data = response.json()
        assert response_data['total_matches'] == 2
        assert response_data['total_returned'] == 2
        assert response_data['page_size'] == 0
        assert response_data['page_number'] == 1

        for input_data, expected in zip(company_input_data['searchCandidates'], response_data['results']):
            assert extract_company_data(input_data) == expected

    def test_api_with_bad_query(self, client):
        user = get_user_model().objects.create(email='test@test.com', is_active=True)
        token = Token.objects.create(user=user)

        response = client.post(reverse('api:company-search'),
                               {},
                               content_type='application/json',
                               HTTP_AUTHORIZATION=f'Token {token.key}')

        assert response.status_code == 400

        expected_response = {
            'non_field_errors': ["At least one standalone field required: ['duns_number', 'search_term']."]
        }
        assert response.json() == expected_response

    def test_query_duns_number_updates_local_db_and_monitoring_is_enabled(
        self,
        client,
        mocker,
        company_list_api_response_json,
    ):
        user = get_user_model().objects.create(email='test@test.com', is_active=True)
        token = Token.objects.create(user=user)

        company_input_data = json.loads(company_list_api_response_json)
        company_input_data['searchCandidates'].pop()
        company_input_data['candidatesReturnedQuantity'] = 1
        company_input_data['candidatesMatchedQuantity'] = 1

        mock_api_request = mocker.patch('dnb_direct_plus.api.api_request')
        mock_api_request.return_value.json.return_value = company_input_data

        assert Company.objects.count() == 0
        response = client.post(
            reverse('api:company-search'),
            {'duns_number': company_input_data['searchCandidates'][0]['organization']['duns']},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {token.key}'
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
    def test_last_updated_field(self, client):
        user = get_user_model().objects.create(email='test@test.com', is_active=True)
        token = Token.objects.create(user=user)

        CompanyFactory(last_updated=timezone.now() - datetime.timedelta(1))
        company = CompanyFactory(last_updated=timezone.now() + datetime.timedelta(1))
        expected_company_data = CompanySerialiser(company).data

        response = client.get(reverse('api:company-updates'),
                              {'last_updated_after': self._iso_now()},
                              content_type='application/json',
                              HTTP_AUTHORIZATION=f'Token {token.key}')

        assert response.status_code == 200
        assert response.json() == {
            'next': None,
            'previous': None,
            'count': 1,
            'results': [
                expected_company_data
            ],
        }

    def test_last_updated_invalid_date_results_in_400(self, client):
        user = get_user_model().objects.create(email='test@test.com', is_active=True)
        token = Token.objects.create(user=user)

        response = client.get(reverse('api:company-updates'),
                              {'last_updated_after': 'is-not-a-date'},
                              content_type='application/json',
                              HTTP_AUTHORIZATION=f'Token {token.key}')

        assert response.status_code == 400
        assert response.json() == {'detail': 'Invalid date: is-not-a-date'}

    def test_no_params_returns_all_results(self, client):
        duns_numbers = [CompanyFactory().duns_number, CompanyFactory().duns_number]

        user = get_user_model().objects.create(email='test@test.com', is_active=True)
        token = Token.objects.create(user=user)

        response = client.get(reverse('api:company-updates'),
                              {},
                              content_type='application/json',
                              HTTP_AUTHORIZATION=f'Token {token.key}')

        assert response.status_code == 200

        result_data = response.json()
        assert len(result_data['results']) == 2
        assert result_data['count'] == 2
        assert all(result['duns_number'] in duns_numbers for result in result_data['results'])

    @freeze_time('2019-11-25 12:00:01 UTC')
    def test_pagination(self, client):
        user = get_user_model().objects.create(email='test@test.com', is_active=True)
        token = Token.objects.create(user=user)

        company1 = CompanyFactory(last_updated=timezone.now() + datetime.timedelta(1))
        company2 = CompanyFactory(last_updated=timezone.now() + datetime.timedelta(2))

        response = client.get(reverse('api:company-updates'),
                              {'last_updated_after': self._iso_now(), 'page_size': 1},
                              content_type='application/json',
                              HTTP_AUTHORIZATION=f'Token {token.key}')

        assert response.status_code == 200
        response_data = response.json()
        assert response_data['next'] is not None
        assert len(response_data['results']) == 1
        assert response_data['count'] == 2
        assert response_data['results'][0]['duns_number'] == company1.duns_number

        response = client.get(response_data['next'],
                              content_type='application/json',
                              HTTP_AUTHORIZATION=f'Token {token.key}')

        assert response.status_code == 200
        response_data = response.json()
        assert response_data['next'] is None
        assert len(response_data['results']) == 1
        assert response_data['results'][0]['duns_number'] == company2.duns_number
