from rest_framework import generics

from company.models import Company
from .serialisers import WorkspaceCompanySerialiser


class CompanyListApiView(generics.ListAPIView):
    serializer_class = WorkspaceCompanySerialiser
    queryset = Company.objects.filter(worldbase_source__isnull=False)
