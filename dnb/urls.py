from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .viewsets import CompanyDocumentViewSet

router = DefaultRouter()
router.register(r'companies', CompanyDocumentViewSet, base_name='company')

urlpatterns = [
    path('', include(router.urls)),
]
