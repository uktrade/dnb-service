from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from requests.exceptions import HTTPError
from rest_framework import status

from dnb_api.client import api_request, DNB_COMPANY_SEARCH_ENDPOINT
from dnb_api.constants import SEARCH_QUERY_TO_DNB_FIELD_MAPPING
from dnb_api.mapping import extract_company_data


class DNBCompanySearchApiView(APIView):
    """An API view that proxies requests to Dun & Bradstreet's CompanyList search."""

    permission_classes = (IsAuthenticated,)

    def post(self, request):

        data = request.data.copy()
        data.setdefault('page_size', 10)
        data.setdefault('page_number', 1)

        query = {
            SEARCH_QUERY_TO_DNB_FIELD_MAPPING[k]: v for k, v in data.items()
        }

        try:
            response = api_request('POST', DNB_COMPANY_SEARCH_ENDPOINT, json=query)
        except HTTPError as ex:
            if ex.response.status_code == 404:
                results = {
                    'total_matches': 0,
                    'total_returned': 0,
                    'page_size': 0,
                    'page_number': 0,
                    'results': [],
                }
                return Response(results)

            elif ex.response.status_code == 400:
                error_detail = ex.response.json()['error']
                return Response(error_detail, status=status.HTTP_400_BAD_REQUEST)

        response_data = response.json()
        # import pdb; pdb.set_trace()
        results = [extract_company_data(item) for item in response_data['searchCandidates']]

        output = {
            'total_matches': response_data['candidatesMatchedQuantity'],
            'total_returned': response_data['candidatesReturnedQuantity'],
            'page_size': response_data['inquiryDetail']['pageSize'],
            'page_number': response_data['inquiryDetail']['pageNumber'],
            'results': results,
        }

        return Response(output)
