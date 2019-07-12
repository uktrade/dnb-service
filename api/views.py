from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from requests.exceptions import HTTPError


from dnb_api.client import api_request, DNB_COMPANY_SEARCH_ENDPOINT
from dnb_api.constants import SEARCH_QUERY_TO_DNB_FIELD_MAPPING
from dnb_api.mapping import extract_company_data


class DNBCompanySearchApiView(APIView):
    """An API view that proxies requests to Dun & Bradstreet's CompanyList search."""

    #permission_classes = (IsAuthenticated,)

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
                raise NotFound(detail='No results for query', code=404)
            else:
                raise

        results = [extract_company_data(item) for item in response.json()['searchCandidates']]

        return Response(results)
