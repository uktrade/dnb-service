import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse

from requests.exceptions import HTTPError
from rest_framework.authtoken.models import Token


class TestCompanySearchView:
    def test_requires_authentication(self, client):
        response = client.get(reverse('api:company-search'))

        assert response.status_code == 401

    @pytest.mark.django_db
    def test_404_returns_empty_data(self, client, mocker):

        user = get_user_model().objects.create(email='test@test.com', is_active=True)
        token = Token.objects.create(user=user)

        mock_api_request = mocker.patch('api.views.api_request')
        mock_api_request.side_effect = HTTPError(response=mocker.Mock(status_code=404))

        response = client.post(reverse('api:company-search'),
                               content_type='application/json',
                               HTTP_AUTHORIZATION=f'Token {token.key}')

        assert response.status_code == 200
        assert response.json() == {
            'total_matches': 0,
            'total_returned': 0,
            'page_size': 0,
            'page_number': 0,
            'results': []
        }
