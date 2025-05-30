import logging

logger = logging.getLogger(__name__)

from requests.exceptions import HTTPError

from dnb_direct_plus.client import api_request
from dnb_direct_plus.constants import (
    DEPRECATED_SEARCH_QUERY_PARAMS_V2,
    SEARCH_QUERY_TO_DNB_FIELD_MAPPING,
    SEARCH_QUERY_TO_DNB_FIELD_MAPPING_V2,
)
from dnb_direct_plus.mapping import extract_company_data
from dnb_direct_plus.tasks import update_company_and_enable_monitoring

DNB_COMPANY_SEARCH_ENDPOINT = "/v1/search/companyList"
DNB_COMPANY_SEARCH_ENDPOINT_V2 = "/v1/match/cleanseMatch"
DNB_COMPANY_HIERARCHY_ENDPOINT = "v1/familyTree"

company_endpoint_from_duns = lambda dunsNumber: f"/v1/data/duns/{dunsNumber}"


def company_list_search(query, update_local=False):
    """
    Perform a DNB Direct+ company search list api call

    query parameters are supplied in a local format see `SEARCH_QUERY_TO_DNB_FIELD_MAPPING` in constants.py

    only a subset of fields are extracted and mapped to a local format.

    Documentation for the DNB api call is available here:
    https://directplus.documentation.dnb.com/openAPI.html?apiID=searchCompanyList
    """
    mapped_query = {SEARCH_QUERY_TO_DNB_FIELD_MAPPING[k]: v for k, v in query.items()}

    try:
        response = api_request("POST", DNB_COMPANY_SEARCH_ENDPOINT, json=mapped_query)
    except HTTPError as ex:
        if ex.response.status_code == 404:
            response_data = {}
        else:
            raise
    else:
        response_data = response.json()

    results = [
        extract_company_data(item) for item in response_data.get("searchCandidates", [])
    ]

    # update the local company record and enable monitoring
    if update_local and "duns_number" in query and len(results) == 1:
        update_company_and_enable_monitoring(response_data["searchCandidates"][0])

    return {
        "total_matches": response_data.get("candidatesMatchedQuantity", 0),
        "total_returned": response_data.get("candidatesReturnedQuantity", 0),
        "page_size": response_data.get("inquiryDetail", {}).get("pageSize", 0),
        "page_number": response_data.get("inquiryDetail", {}).get("pageNumber", 1),
        "results": results,
    }


def company_list_request_v2(query):
    """
    Request logic for company_list_search_v2()
    """
    query_keys = list(query.keys())
    for parameter in query_keys:
        if parameter in DEPRECATED_SEARCH_QUERY_PARAMS_V2:
            logger.warning(
                f"parameter '{parameter}' is deprecated in v2 of company list search and has been ignored"
            )
            query.pop(parameter, None)

    mapped_query = {
        SEARCH_QUERY_TO_DNB_FIELD_MAPPING_V2[k]: v for k, v in query.items()
    }

    try:
        response = api_request(
            "GET", DNB_COMPANY_SEARCH_ENDPOINT_V2, params=mapped_query
        )
    except HTTPError as ex:
        logger.exception("HTTP error occurred")
        if ex.response.status_code == 404:
            return {}
        else:
            raise
    else:
        return response.json()


def company_by_duns(duns):
    try:
        response = api_request(
            "GET",
            company_endpoint_from_duns(duns),
            params={"productId": "cmpelk", "versionId": "v1"},
        )
    except HTTPError as ex:
        logger.exception("HTTP error occurred")
        if ex.response.status_code == 404:
            return {}
        else:
            raise
    else:
        return response.json()


def company_list_search_v2(query, update_local=False):
    """
    Tries to return the best match for the search terms using the DNB Direct+ cleanseMatch endpoint

    query parameters are supplied in a local format see `SEARCH_QUERY_TO_DNB_FIELD_MAPPING_V2` in constants.py

    some query parameters are accepted but ignored as they are no longer applicable to v2, see `DEPRECATED_SEARCH_QUERY_PARAMS_V2` in constants.py

    only a subset of fields are extracted and mapped to a local format.

    Documentation for the DNB api call is available here:
    https://directplus.documentation.dnb.com/openAPI.html?apiID=IDRCleanseMatch
    """
    response_data = company_list_request_v2(query)
    results = [
        extract_company_data(item) for item in response_data.get("matchCandidates", [])
    ]

    # update the local company record with up to date information and enable monitoring
    if update_local and "duns_number" in query and len(results) == 1:
        duns_number = query["duns_number"]
        company = company_by_duns(duns_number)
        update_company_and_enable_monitoring(company)
        results = [extract_company_data(company)]

        return {
            "results": results,
        }

    else:
        return {
            "results": results,
        }


def company_hierarchy_list_initial_request(query):
    """
    Request logic for company_hierarchy_list_search()
    """
    query_keys = list(query.keys())
    for parameter in query_keys:
        if parameter in DEPRECATED_SEARCH_QUERY_PARAMS_V2:
            logger.warning(
                f"parameter '{parameter}' is deprecated in v2 of company list search and has been ignored"
            )
            query.pop(parameter, None)

    mapped_query = {
        SEARCH_QUERY_TO_DNB_FIELD_MAPPING_V2[k]: v for k, v in query.items()
    }

    url = f"{DNB_COMPANY_HIERARCHY_ENDPOINT}/{mapped_query['duns']}"

    response = company_hierarchy_api_request(url)

    return response


def company_hierarchy_api_request(url):
    """
    Request logic for company_hierarchy_list_search()

    Returns:
        dict: Company hierarchy data if found, empty dict if not

    Raises:
        HTTPError: For non-404 HTTP errors
    """
    try:
        response = api_request("GET", url)
        return response.json()

    except HTTPError as ex:
        status_code = ex.response.status_code
        error_json = ex.response.json()['error']

        if status_code == 404:
            logger.info(
                f'Company hierarchy not found - {url} - '
                f'D&B error {error_json['errorCode']}: {error_json['errorMessage']}'
            )
            return {}

        else:
            logger.error(f'D&B error {error_json['errorCode']}: {error_json['errorMessage']}')
            raise


def company_hierarchy_list_search(query):
    """
    Returns the full hierarchy for a specific duns number.

    Documentation for the DNB api call is available here:
    https://directplus.documentation.dnb.com/html/resources/JSONSample_FamTree.html
    """
    response_data = company_hierarchy_list_initial_request(query)

    if not response_data:
        return {"family_tree_members": []}

    company_hierarchy = {
        "global_ultimate_duns": response_data["globalUltimateDuns"],
        "global_ultimate_family_tree_members_count": response_data[
            "globalUltimateFamilyTreeMembersCount"
        ],
        "branches_excluded_members_count": response_data[
            "branchesExcludedMembersCount"
        ],
        "family_tree_members": response_data["familyTreeMembers"],
    }

    is_next = "next" in response_data["links"]

    while is_next:
        response_data = company_hierarchy_api_request(response_data["links"]["next"])
        for familyTreeMember in response_data["familyTreeMembers"]:
            company_hierarchy["family_tree_members"].append(familyTreeMember)
        is_next = "next" in response_data["links"]

    return company_hierarchy


def company_hierarchy_count(query):
    """
    Returns the count of companies for the duns number in the hierarchy
    """
    response_data = company_hierarchy_count_request(query)

    if not response_data:
        return 0
    
    return response_data.get('globalUltimateFamilyTreeMembersCount', 0)


def company_hierarchy_count_request(query):
    """
    Request logic for company_hierarchy_count_request
    """
    query_keys = list(query.keys())
    for parameter in query_keys:
        if parameter in DEPRECATED_SEARCH_QUERY_PARAMS_V2:
            logger.warning(
                f"parameter '{parameter}' is deprecated in v2 of company list search and has been ignored"
            )
            query.pop(parameter, None)

    mapped_query = {
        SEARCH_QUERY_TO_DNB_FIELD_MAPPING_V2[k]: v for k, v in query.items()
    }
    
    url = f"{DNB_COMPANY_HIERARCHY_ENDPOINT}/{mapped_query['duns']}?page[size]=1"
    
    try:
        response = api_request(
            "GET", url
        )
    except HTTPError as ex:
        if ex.response.status_code == 404:
            logger.info("404 error occurred, returning 0")
            return 0
        else:
            raise
    else:
        return response.json()