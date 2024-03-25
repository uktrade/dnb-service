from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from core.admin_views import admin_login_view
from health_check.views import HealthCheckP1View

auth_urls = []

if settings.ENABLE_STAFF_SSO:
    auth_urls = [
        path('auth/', include('authbroker_client.urls', namespace='authbroker')),
        path('admin/login/', admin_login_view),
    ]

urlpatterns = [
    *auth_urls,
    path('admin/', admin.site.urls),
    path('api/workspace/', include('workspace.urls', namespace='workspace')),
    path('api/', include('api.urls', namespace='api')),
    path('healthcheck/', include('health_check.urls', namespace='healthcheck')),
    path('pingdom/ping.xml', HealthCheckP1View.as_view(), name='pingdom'),
    path('', include('django_prometheus.urls')),
]
