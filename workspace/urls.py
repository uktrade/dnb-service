from django.urls import path

from .views import CompanyListApiView

app_name = 'workspace_api'

urlpatterns = [
    path('companies/', CompanyListApiView.as_view(), name='company-list'),
]
