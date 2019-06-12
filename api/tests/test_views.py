import pytest

from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.authtoken.models import Token


class TestCompanySearchView:
    def test_requires_authentication(self, client):
        response = client.get(reverse('api:company-search'))

        assert response.status_code == 401

    @pytest.mark.django_db
    def test_request_requires_body(self, client):
        user = get_user_model().objects.create(email='test@test.com', is_active=True)
        token = Token.objects.create(user=user)

        response = client.get(reverse('api:company-search'), HTTP_AUTHORIZATION=f'Token {token.key}')

        assert response.status_code == 400
