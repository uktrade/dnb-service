import pytest

from django.contrib.auth import get_user_model


class TestAdminSSOLogin:

    def setup_method(self):
        self.user = get_user_model().objects.create(
            email='test@test.com',
            is_staff=False,
            is_superuser=False
        )

    @pytest.mark.django_db
    def test_login_authenticated_but_not_staff_leads_to_403(self, client):
        client.force_login(self.user)
        response = client.get('/admin/login/')

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_login_authenticated_without_next_url_redirects_to_admin(self, client):
        self.user.is_staff = True
        self.user.save()
        client.force_login(self.user)

        response = client.get('/admin/login/')

        assert response.status_code == 302
        assert response.url == '/admin/'

    @pytest.mark.django_db
    def test_login_authenticated_redirects_to_next_url(self, client):
        self.user.is_staff = True
        self.user.save()

        session = client.session
        session['admin_next_url'] = '/whatever/'
        session.save()
        client.force_login(self.user)

        response = client.get('/admin/login/')

        assert response.status_code == 302
        assert response.url == '/whatever/'

    @pytest.mark.django_db
    def test_login_redirects_to_sso_login(self, client):
        response = client.get('/admin/login/')

        assert response.status_code == 302
        assert response.url == '/auth/login/'

    @pytest.mark.django_db
    def test_login_saves_next_query_string_in_session(self, client):
        session = client.session
        client.get('/admin/login/?next=/whatever/')

        assert session['admin_next_url'] == '/whatever/'
