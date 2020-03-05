from django.urls import path

from .views import ChangeRequestApiView, CompanyUpdatesApiView, DNBCompanySearchApiView

app_name = 'api'

urlpatterns = [
    path('companies/', CompanyUpdatesApiView.as_view(), name='company-updates'),
    path('companies/search/', DNBCompanySearchApiView.as_view(), name='company-search'),
    path('change-request/', ChangeRequestApiView.as_view(), name='change-request'),
]
