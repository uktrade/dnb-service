from core.middleware import AdminIpRestrictionMiddleware

from django.http import HttpResponse
from django.urls import reverse


def dummy_view(_):
    return HttpResponse(status=200)


class TestAdminIpRestrictionMiddleware:
    def test_middleware_is_enabled(self, client, settings):
        settings.RESTRICT_ADMIN = True
        assert client.get(reverse('admin:index')).status_code == 401

    def test_applies_to_admin_only(self, rf, settings):

        # TODO: point this test at valid view when one is added.

        settings.RESTRICT_ADMIN = True

        request = rf.get('/')

        assert AdminIpRestrictionMiddleware(dummy_view)(request).status_code == 200

    def test_not_enabled_if_restrict_admin_is_false(self, rf, settings):
        settings.RESTRICT_ADMIN = False

        request = rf.get(reverse('admin:index'), HTTP_X_FORWARDED_FOR='')

        assert AdminIpRestrictionMiddleware(dummy_view)(request).status_code == 200

    def test_missing_x_forwarded_header(self, rf, settings):
        settings.RESTRICT_ADMIN = True

        request = rf.get(reverse('admin:index'), HTTP_X_FORWARDED_FOR='1.1.1.1')

        assert AdminIpRestrictionMiddleware(dummy_view)(request).status_code == 401

    def test_with_invalid_x_forwarded_header(self, rf, settings):
        settings.RESTRICT_ADMIN = True

        request = rf.get(reverse('admin:index'), HTTP_X_FORWARDED_FOR='1.1.1.1')

        assert AdminIpRestrictionMiddleware(dummy_view)(request).status_code == 401

    def test_with_valid_ip(self, rf, settings):
        settings.RESTRICT_ADMIN = True
        settings.ALLOWED_ADMIN_IPS = ['2.2.2.2']

        request = rf.get(reverse('admin:index'),
                         HTTP_X_FORWARDED_FOR='1.1.1.1, 2.2.2.2, 3.3.3.3')

        assert AdminIpRestrictionMiddleware(dummy_view)(request).status_code == 200

    def test_with_invalid_ip(self, rf, settings):
        settings.RESTRICT_ADMIN = True
        settings.ALLOWED_ADMIN_IPS = ['1.1.1.1']

        request = rf.get(reverse('admin:index'),
                         HTTP_X_FORWARDED_FOR='1.1.1.1, 2.2.2.2, 3.3.3.3')
        # import pdb; pdb.set_trace()
        assert AdminIpRestrictionMiddleware(dummy_view)(request).status_code == 401

        settings.ALLOWED_ADMIN_IPS = ['3.3.3.3']

        assert AdminIpRestrictionMiddleware(dummy_view)(request).status_code == 401
