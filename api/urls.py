from django.urls import path

from .views import ChangeRequestAPIView, CompanyUpdatesAPIView, DNBCompanySearchAPIView

app_name = 'api'

urlpatterns = [
    path('companies/', CompanyUpdatesAPIView.as_view(), name='company-updates'),
    path('companies/search/', DNBCompanySearchAPIView.as_view(), name='company-search'),
    path('change-request/', ChangeRequestAPIView.as_view(), name='change-request'),
]
