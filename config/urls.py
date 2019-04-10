from core.admin_views import admin_login_view

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('auth/', include('authbroker_client.urls', namespace='authbroker')),
    path('admin/login/', admin_login_view),
    path('admin/', admin.site.urls),
]
