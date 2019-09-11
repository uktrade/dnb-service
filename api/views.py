from dnb_direct_plus.api import company_list_search

from requests.exceptions import HTTPError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serialisers import CompanySearchInputSerialiser


class DNBCompanySearchApiView(APIView):
    """An API view that proxies requests to Dun & Bradstreet's CompanyList search."""

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serialiser = CompanySearchInputSerialiser(data=request.data)
        serialiser.is_valid(raise_exception=True)

        try:
            data = company_list_search(serialiser.data)
        except HTTPError as ex:
            error_detail = ex.response.json()['error']
            return Response(error_detail, status=ex.response.status_code)

        return Response(data)
