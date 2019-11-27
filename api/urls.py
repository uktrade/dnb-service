from django.urls import path

from .views import CompanyUpdatesApiView, DNBCompanySearchApiView

app_name = 'api'

urlpatterns = [
    path('companies/', CompanyUpdatesApiView.as_view(), name='company-updates'),
    path('companies/search/', DNBCompanySearchApiView.as_view(), name='company-search'),
]
