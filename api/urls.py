from django.urls import path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

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
    re_path(r"^swagger\.(?P<format>json|yaml)$", SpectacularAPIView.as_view(), name="schema-json"),
    re_path(r"^swagger/$", SpectacularSwaggerView.as_view(url_name='api:schema-json'), name="schema-swagger-ui"),
]
