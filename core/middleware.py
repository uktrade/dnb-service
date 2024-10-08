import logging
from ipaddress import ip_address, ip_network

from django.conf import settings
from django.http import HttpResponse
from django.urls import resolve, reverse
from django.urls.exceptions import Resolver404

logger = logging.getLogger(__name__)


def _is_valid_ip(client_ip):
    if not client_ip:
        return False

    if client_ip in settings.ALLOWED_IPS:
        return True

    ip_addr = ip_address(client_ip)
    for cidr in settings.ALLOWED_IP_RANGES:
        if ip_addr in ip_network(cidr):
            return True

    return False


def _get_client_ip(request):
    client_ip_index = getattr(settings, 'IP_SAFELIST_XFF_INDEX', -2)

    try:
        return request.headers['x-forwarded-for'].split(',')[client_ip_index].strip()
    except (IndexError, KeyError):
        logger.warning(
            'X-Forwarded-For header is missing or does not '
            'contain enough elements to determine the '
            'client\'s ip')  # noqa: Q003
        return None


def IpRestrictionMiddleware(get_response):

    def middleware(request):

        try:
            app_name = resolve(request.path).app_name
        except Resolver404:
            app_name = None

        restricted_paths = [reverse(path) for path in getattr(settings, 'IP_RESTRICT_PATH_NAMES', [])]

        if settings.IP_RESTRICT and app_name in settings.IP_RESTRICT_APPS or request.path in restricted_paths:
            client_ip = _get_client_ip(request)
            if not _is_valid_ip(client_ip):
                return HttpResponse('Unauthorized', status=401)

        return get_response(request)

    return middleware
