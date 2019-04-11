import pytest

from core.middleware import AdminIpRestrictionMiddleware

from django.http import HttpResponse


def test_ip_restriction_middleware_is_enabled(client, settings):
    settings.RESTRICT_ADMIN = True
    assert client.get('/admin/').status_code == 401


def dummy_view(_):
    return HttpResponse(status=200)


@pytest.mark.skip(reason='currently no other routes to test this logic')
def test_ip_restriction_applies_to_admin_only(rf, settings):
    settings.RESTRICT_ADMIN = True

    request = rf.get('/')

    assert AdminIpRestrictionMiddleware(dummy_view)(request).status_code == 200


def test_ip_restriction_enabled_false(rf, settings):
    settings.RESTRICT_ADMIN = False

    request = rf.get('/admin/', HTTP_X_FORWARDED_FOR='')

    assert AdminIpRestrictionMiddleware(dummy_view)(request).status_code == 200


def test_ip_restriction_missing_x_forwarded_header(rf, settings):
    settings.RESTRICT_ADMIN = True

    request = rf.get('/admin/', HTTP_X_FORWARDED_FOR='1.1.1.1')

    assert AdminIpRestrictionMiddleware(dummy_view)(request).status_code == 401


def test_ip_restriction_invalid_x_forwarded_header(rf, settings):
    settings.RESTRICT_ADMIN = True

    request = rf.get('/admin/', HTTP_X_FORWARDED_FOR='1.1.1.1')

    assert AdminIpRestrictionMiddleware(dummy_view)(request).status_code == 401


def test_ip_restriction_valid_ip(rf, settings):
    settings.RESTRICT_ADMIN = True
    settings.ALLOWED_ADMIN_IPS = ['2.2.2.2']

    request = rf.get('/admin/',
                     HTTP_X_FORWARDED_FOR='1.1.1.1, 2.2.2.2, 3.3.3.3')

    assert AdminIpRestrictionMiddleware(dummy_view)(request).status_code == 200


def test_ip_restriction_invalid_ip(rf, settings):
    settings.RESTRICT_ADMIN = True
    settings.ALLOWED_ADMIN_IPS = ['1.1.1.1']

    request = rf.get('/admin/',
                     HTTP_X_FORWARDED_FOR='1.1.1.1, 2.2.2.2, 3.3.3.3')

    assert AdminIpRestrictionMiddleware(dummy_view)(request).status_code == 401

    settings.ALLOWED_ADMIN_IPS = ['3.3.3.3']

    assert AdminIpRestrictionMiddleware(dummy_view)(request).status_code == 401
