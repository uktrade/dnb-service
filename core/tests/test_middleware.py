import pytest

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

    @pytest.mark.parametrize(
        'xff_header,expected_status', (
            [
                '1.1.1.1, 2.2.2.2, 3.3.3.3', 200
            ],
            [
                '1.1.1.1', 401
            ],
            [
                '', 401,
            ]
        )
    )
    def test_x_forwarded_header(self, rf, settings, xff_header, expected_status):
        settings.RESTRICT_ADMIN = True

        settings.ALLOWED_ADMIN_IPS = ['2.2.2.2']

        request = rf.get(reverse('admin:index'), HTTP_X_FORWARDED_FOR=xff_header)

        assert AdminIpRestrictionMiddleware(dummy_view)(request).status_code == expected_status

    @pytest.mark.parametrize(
        'allowed_ips,expected_status', (
            [
                ['2.2.2.2'], 200
            ],
            [
                ['1.1.1.1'], 401
            ]
        )
    )
    def test_ips(self, rf, settings, allowed_ips, expected_status):
        settings.RESTRICT_ADMIN = True
        settings.ALLOWED_ADMIN_IPS = allowed_ips

        request = rf.get(reverse('admin:index'),
                         HTTP_X_FORWARDED_FOR='1.1.1.1, 2.2.2.2, 3.3.3.3')

        assert AdminIpRestrictionMiddleware(dummy_view)(request).status_code == expected_status

        settings.ALLOWED_ADMIN_IPS = ['3.3.3.3']

        assert AdminIpRestrictionMiddleware(dummy_view)(request).status_code == 401
