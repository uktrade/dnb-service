from django.urls import path

from .views import HealthCheckP1View


app_name = 'health_check'


urlpatterns = [
    path('check/', HealthCheckP1View.as_view(), name='p1'),
]
