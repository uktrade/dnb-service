from django.conf.urls import url
from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="dnb service API",
        default_version="v1",
        description="API documentation for the dnb service endpoints",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

from api.views import (
    ChangeRequestAPIView,
    CompanyUpdatesAPIView,
    DNBCompanyHierarchySearchAPIView,
    DNBCompanyHierarchySearchCountAPIView,
    DNBCompanySearchAPIView,
    DNBCompanySearchV2APIView,
    InvestigationAPIView,
)

app_name = "api"

urlpatterns = [
    path("companies/search/", DNBCompanySearchAPIView.as_view(), name="company-search"),
    path(
        "v2/companies/search/",
        DNBCompanySearchV2APIView.as_view(),
        name="company-search-v2",
    ),
    path(
        "companies/hierarchy/search/",
        DNBCompanyHierarchySearchAPIView.as_view(),
        name="company-hierarchy-search",
    ),
    path(
        "companies/hierarchy/search/count",
        DNBCompanyHierarchySearchCountAPIView.as_view(),
        name="company-hierarchy-search-count",
    ),
    path("companies/", CompanyUpdatesAPIView.as_view(), name="company-updates"),
    path("change-request/", ChangeRequestAPIView.as_view(), name="change-request"),
    path("investigation/", InvestigationAPIView.as_view(), name="investigation"),
    url(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    url(
        r"^swagger/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
]
