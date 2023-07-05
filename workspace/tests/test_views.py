import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token

from company.tests.factories import CompanyFactory

pytestmark = pytest.mark.django_db


class TestCompanyListView:
    def test_requires_authentication(self, client):
        response = client.get(reverse('workspace:company-list'))

        assert response.status_code == 401

    def test_response(self, client):
        CompanyFactory(
            primary_name='acme limited',
            duns_number='000000020',
            source={'for': 'bar'},
            worldbase_source={'bar': 'baz'}
        )

        user = get_user_model().objects.create(email='test@test.com', is_active=True)
        token = Token.objects.create(user=user)

        response = client.get(reverse('workspace:company-list'),
                              {},
                              content_type='application/json',
                              HTTP_AUTHORIZATION=f'Token {token.key}')

        assert response.status_code == 200
        result_data = response.json()
        assert len(result_data['results']) == 1

        assert result_data['results'][0] == {
            'last_updated': None,
            'duns_number': '000000020',
            'parent_duns_number': None,
            'global_ultimate_duns_number': '',
            'primary_name': 'acme limited',
            'global_ultimate_primary_name': '',
            'trading_names': [],
            'domain': '',
            'address_line_1': '',
            'address_line_2': '',
            'address_town': '',
            'address_county': '',
            'address_area_abbrev_name': '',
            'address_area_name': '',
            'address_country': 'AF',
            'address_postcode': '',
            'registered_address_line_1': '',
            'registered_address_line_2': '',
            'registered_address_town': '',
            'registered_address_county': '',
            'registered_address_area_abbrev_name': '',
            'registered_address_area_name': '',
            'registered_address_country': None,
            'registered_address_postcode': '',
            'line_of_business': '',
            'is_out_of_business': False,
            'year_started': 2000,
            'employee_number': None,
            'is_employees_number_estimated': None,
            'annual_sales': None,
            'annual_sales_currency': '',
            'is_annual_sales_estimated': None,
            'legal_status': 'corporation',
            'registration_numbers': [],
            'primary_industry_codes': [],
            'industry_codes': [],
            'worldbase_source': {'bar': 'baz'},
            'source': {'for': 'bar'}
        }

    def test_worldbase_source_field_is_required(self, client):
        user = get_user_model().objects.create(email='test@test.com', is_active=True)
        token = Token.objects.create(user=user)

        CompanyFactory(worldbase_source=None)

        response = client.get(
            reverse('api:company-updates'),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {token.key}'
        )

        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data['results']) == 0
