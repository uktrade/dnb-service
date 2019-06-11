import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


pytestmark = [
    pytest.mark.django_db
]


class TestUserManager:
    def test_create_user_without_email_raises_value_error(self):
        with pytest.raises(ValueError):
            User.objects.create_user(None, 'a-password')

    def test_create_user(self):
        user = User.objects.create_user('test@test.com', 'password')

        assert user.email == 'test@test.com'
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_superuser(self):
        user = User.objects.create_superuser('test@test.com', 'password')

        assert user.email == 'test@test.com'
        assert user.is_staff
        assert user.is_superuser
