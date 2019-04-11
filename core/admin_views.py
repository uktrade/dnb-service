from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import is_safe_url


def admin_login_view(request):
    """A replacement admin login view that will direct the user through the SSO
    authentication flow. """

    next_url = request.GET.get(
        'next',
        request.session.get('admin_next_url', None))

    if next_url and not is_safe_url(next_url, settings.ALLOWED_HOSTS):
        next_url = False

    if not next_url:
        next_url = reverse('admin:index')

    if request.user.is_authenticated:
        if not request.user.is_staff:
            raise PermissionDenied
        else:
            if 'admin_next_url' in request.session:
                del request.session['admin_next_url']

            return redirect(next_url)
    else:
        request.session['admin_next_url'] = next_url

        return redirect('authbroker:login')
