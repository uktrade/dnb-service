from django.urls import path

from api.views import (
    ChangeRequestAPIView,
    CompanyUpdatesAPIView,
    DNBCompanySearchAPIView,
    DNBCompanySearchV2APIView,
    InvestigationAPIView,
)

app_name = 'api'

urlpatterns = [
    path('companies/search/', DNBCompanySearchAPIView.as_view(), name='company-search'),
    path('v2/companies/search/', DNBCompanySearchV2APIView.as_view(), name='company-search-v2'),
    path('companies/', CompanyUpdatesAPIView.as_view(), name='company-updates'),
    path('change-request/', ChangeRequestAPIView.as_view(), name='change-request'),
    path('investigation/', InvestigationAPIView.as_view(), name='investigation'),
]
