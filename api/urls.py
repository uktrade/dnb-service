from django.urls import include, path

from .views import CompanySearchApiView

app_name = 'api'

urlpatterns = [
    path('companies/search/', CompanySearchApiView.as_view(), name='company-search'),
]
