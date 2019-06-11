from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import is_safe_url

ADMIN_REDIRECT_URL_SESSION_KEY = 'admin_next_url'


def admin_login_view(request):
    """A replacement admin login view that will direct the user through the SSO
    authentication flow. """

    next_url = request.GET.get(
        REDIRECT_FIELD_NAME,
        request.session.get(ADMIN_REDIRECT_URL_SESSION_KEY, None))

    if next_url and not is_safe_url(next_url, settings.ALLOWED_HOSTS, require_https=request.is_secure()):
        next_url = None

    if not next_url:
        next_url = reverse('admin:index')

    if request.user.is_authenticated:
        if not request.user.is_staff:
            raise PermissionDenied
        else:
            if ADMIN_REDIRECT_URL_SESSION_KEY in request.session:
                del request.session[ADMIN_REDIRECT_URL_SESSION_KEY]

            return redirect(next_url)
    else:
        request.session[ADMIN_REDIRECT_URL_SESSION_KEY] = next_url

        return redirect('authbroker:login')
