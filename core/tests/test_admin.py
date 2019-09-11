import pytest
from django.contrib.auth import get_user_model, REDIRECT_FIELD_NAME
from django.urls import reverse

from core.admin_views import ADMIN_REDIRECT_URL_SESSION_KEY

pytestmark = [
    pytest.mark.django_db
]


class TestAdminSSOLogin:

    def setup_method(self):
        self.user = get_user_model().objects.create(
            email='test@test.com',
            is_staff=False,
            is_superuser=False
        )

    def test_login_authenticated_but_not_staff_leads_to_403(self, client):
        client.force_login(self.user)
        response = client.get(reverse('admin:login'))

        assert response.status_code == 403

    def test_login_authenticated_without_next_url_redirects_to_admin(self, client):
        self.user.is_staff = True
        self.user.save()
        client.force_login(self.user)

        response = client.get(reverse('admin:login'))

        assert response.status_code == 302
        assert response.url == reverse('admin:index')

    def test_login_authenticated_redirects_to_next_url(self, client):
        self.user.is_staff = True
        self.user.save()

        session = client.session
        session[ADMIN_REDIRECT_URL_SESSION_KEY] = '/whatever/'
        session.save()
        client.force_login(self.user)

        response = client.get(reverse('admin:login'))

        assert response.status_code == 302
        assert response.url == '/whatever/'

    def test_login_redirects_to_sso_login(self, client):
        response = client.get(reverse('admin:login'))

        assert response.status_code == 302
        assert response.url == reverse('authbroker:login')

    def test_login_saves_next_query_string_in_session(self, client):

        client.get(reverse('admin:login') + f'?{REDIRECT_FIELD_NAME}=/whatever/')

        assert ADMIN_REDIRECT_URL_SESSION_KEY in client.session and \
            client.session[ADMIN_REDIRECT_URL_SESSION_KEY] == '/whatever/'

    def test_next_url_different_domain_not_allowed(self, client, settings):

        self.user.is_staff = True
        self.user.save()

        settings.ALLOWED_HOSTS = ['testserver']

        client.session[ADMIN_REDIRECT_URL_SESSION_KEY] = 'http://somewhereunsafe.com/'
        client.force_login(self.user)

        response = client.get(reverse('admin:login'))

        assert response.status_code == 302
        assert response.url == reverse('admin:index')
