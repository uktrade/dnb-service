import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture()
def auth_client():
    user = User.objects.create(
        email='test@test.com',
        is_active=True
    )
    token = Token.objects.create(user=user)
    return APIClient(
        HTTP_AUTHORIZATION=f'Token {token.key}',
    )
