from django.urls import path

from .views import DNBCompanySearchApiView

app_name = 'api'

urlpatterns = [
    path('companies/search/', DNBCompanySearchApiView.as_view(), name='company-search'),
]
