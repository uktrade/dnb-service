from django.urls import path

from api.views import (
    ChangeRequestAPIView,
    CompanyUpdatesAPIView,
    DNBCompanySearchAPIView,
    InvestigationAPIView,
)

app_name = 'api'

urlpatterns = [
    path('companies/', CompanyUpdatesAPIView.as_view(), name='company-updates'),
    path('companies/search/', DNBCompanySearchAPIView.as_view(), name='company-search'),
    path('change-request/', ChangeRequestAPIView.as_view(), name='change-request'),
    path('investigation/', InvestigationAPIView.as_view(), name='investigation'),
]
