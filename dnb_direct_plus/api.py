from dnb_direct_plus.client import api_request
from dnb_direct_plus.constants import SEARCH_QUERY_TO_DNB_FIELD_MAPPING
from dnb_direct_plus.mapping import extract_company_data

from requests.exceptions import HTTPError


DNB_COMPANY_SEARCH_ENDPOINT = 'https://plus.dnb.com/v1/search/companyList'


def company_list_search(query):
    """
    Perform a DNB Direct+ company search list api call

    query parameters are supplied in a local format see `SEARCH_QUERY_TO_DNB_FIELD_MAPPING` in constants.py

    only a subset of fields are extracted and mapped to a local format.

    Documentation for the DNB api call is available here:
    https://directplus.documentation.dnb.com/openAPI.html?apiID=searchCompanyList
    """
    mapped_query = {
        SEARCH_QUERY_TO_DNB_FIELD_MAPPING[k]: v for k, v in query.items()
    }

    try:
        response = api_request('POST', DNB_COMPANY_SEARCH_ENDPOINT, json=mapped_query)
    except HTTPError as ex:
        if ex.response.status_code == 404:
            response_data = {}
        else:
            raise
    else:
        response_data = response.json()

    results = [extract_company_data(item) for item in response_data.get('searchCandidates', [])]

    return {
        'total_matches': response_data.get('candidatesMatchedQuantity', 0),
        'total_returned': response_data.get('candidatesReturnedQuantity', 0),
        'page_size': response_data.get('inquiryDetail', {}).get('pageSize', 0),
        'page_number': response_data.get('inquiryDetail', {}).get('pageNumber', 1),
        'results': results,
    }
