import datetime

from requests.exceptions import HTTPError
from rest_framework.generics import CreateAPIView, ListAPIView, ListCreateAPIView
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import LimitOffsetPagination

from company.models import ChangeRequest, Company, InvestigationRequest
from company.serialisers import ChangeRequestSerialiser, CompanySerialiser, InvestigationRequestSerializer
from dnb_direct_plus.api import company_list_search, company_list_search_v2
from .serialisers import CompanySearchInputSerialiser, CompanySearchV2InputSerialiser


class DNBCompanySearchAPIView(APIView):
    """
    An API view that proxies requests to Dun & Bradstreet's CompanyList search.
    """

    def post(self, request):
        serialiser = CompanySearchInputSerialiser(data=request.data)
        serialiser.is_valid(raise_exception=True)

        try:
            data = company_list_search(serialiser.data, update_local=True)
        except HTTPError as ex:
            error_detail = ex.response.json()['error']
            return Response(error_detail, status=ex.response.status_code)

        return Response(data)

class DNBCompanySearchV2APIView(APIView):
    """
    An API view that proxies requests to Dun & Bradstreet's cleanseMatch search.
    """
    def post(self, request):
        serialiser = CompanySearchV2InputSerialiser(data=request.data)
        serialiser.is_valid(raise_exception=True)

        try:
            data = company_list_search_v2(serialiser.data, update_local=True)
        except HTTPError as ex:
            error_detail = ex.response.json()['error']
            return Response(error_detail, status=ex.response.status_code)

        return Response(data)


class CompanyUpdatesAPIView(ListAPIView):
    serializer_class = CompanySerialiser

    def get_queryset(self):
        queryset = Company.objects.filter(source__isnull=False)
        last_updated = self.request.query_params.get('last_updated_after', None)

        if last_updated is not None:
            try:
                last_updated = datetime.datetime.fromisoformat(last_updated)
            except ValueError:
                raise ParseError(f'Invalid date: {last_updated}')

            queryset = queryset.filter(last_updated__gte=last_updated)

        return queryset


class ChangeRequestAPIView(ListCreateAPIView):
    """
    Endpoint to save a new ChangeRequest record on POST.
    
    It also retrieves filtered lists of ChangeRequests on GET.
    """
    serializer_class = ChangeRequestSerialiser
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        """
        Filters ChangeRequest records by status and by DUNS number, individually and together.
        """
        queryset = ChangeRequest.objects.all()
        status = self.request.query_params.get('status', None)
        duns_number = self.request.query_params.get('duns_number', None)
        
        if status is not None:
            queryset = queryset.filter(status=status)

        if duns_number is not None:
            queryset = queryset.filter(duns_number=duns_number)

        return queryset

class InvestigationAPIView(CreateAPIView):
    """
    Endpoint to save a new Investigation record on POST.

    At the moment, this will return 501 - Not Implemented.
    """

    queryset = InvestigationRequest.objects.all()
    serializer_class = InvestigationRequestSerializer
