from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from dnb_api.client import company_search


class DNBCompanySearchApiView(APIView):
    """An API view that proxies requests to Dun & Bradstreet's CompanyList search."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):

        # TODO: handle query params

        response = company_search('fuzzy', page_size=10)

        # TODO: transform response into local format

        return Response(response.json())
