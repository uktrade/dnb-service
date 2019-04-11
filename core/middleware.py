import logging

from django.conf import settings
from django.http import HttpResponse
from django.urls import resolve

from .ip_filter import get_client_ip, is_valid_admin_ip


logger = logging.getLogger(__name__)


def AdminIpRestrictionMiddleware(get_response):

    def middleware(request):
        # NOTE: resolve(request.path) may raise a Http404 exception if the route does not exist.
        # In this case the rest of this function's logic will be bypassed.
        if resolve(request.path).app_name == 'admin':
            if settings.RESTRICT_ADMIN:
                client_ip = get_client_ip(request)
                if not client_ip or not is_valid_admin_ip(client_ip):
                    return HttpResponse('Unauthorized', status=401)

        return get_response(request)

    return middleware
