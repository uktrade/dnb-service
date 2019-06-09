from django.contrib import admin
from django.urls import include, path

from core.admin_views import admin_login_view

urlpatterns = [
    path('auth/', include('authbroker_client.urls', namespace='authbroker')),
    path('admin/login/', admin_login_view),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls', namespace='api')),
]
