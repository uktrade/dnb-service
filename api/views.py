import datetime

from rest_framework import generics
from requests.exceptions import HTTPError
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.views import APIView

from .serialisers import CompanySearchInputSerialiser
from company.models import Company
from company.serialisers import CompanySerialiser
from dnb_direct_plus.api import company_list_search
from dnb_direct_plus.monitoring import create_or_update_company


class DNBCompanySearchApiView(APIView):
    """An API view that proxies requests to Dun & Bradstreet's CompanyList search."""

    def post(self, request):
        serialiser = CompanySearchInputSerialiser(data=request.data)
        serialiser.is_valid(raise_exception=True)

        try:
            data = company_list_search(serialiser.data)
        except HTTPError as ex:
            error_detail = ex.response.json()['error']
            return Response(error_detail, status=ex.response.status_code)

        # enable monitoring if the query is against a specific duns number
        if 'duns_number' in serialiser.data:
            create_or_update_company(data)

        return Response(data)


class CompanyUpdatesApiView(generics.ListAPIView):
    serializer_class = CompanySerialiser

    def get_queryset(self):
        queryset = Company.objects.all()
        last_updated = self.request.query_params.get('last_updated_after', None)

        if last_updated is not None:
            try:
                last_updated = datetime.datetime.fromisoformat(last_updated)
            except ValueError:
                raise ParseError(f'Invalid date: {last_updated}')

            queryset = queryset.filter(last_updated__gte=last_updated)

        return queryset
