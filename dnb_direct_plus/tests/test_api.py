import json

import pytest

from requests.exceptions import HTTPError

from company.constants import MonitoringStatusChoices
from company.models import Company

from dnb_direct_plus.api import (
    company_hierarchy_api_request,
    company_hierarchy_count,
    company_hierarchy_list_search,
    company_list_search,
    company_list_search_v2,
)
from ..mapping import extract_company_data


@pytest.mark.django_db
def test_company_list_search(mocker, company_list_api_response_json):
    company_input_data = json.loads(company_list_api_response_json)

    mock_api_request = mocker.patch("dnb_direct_plus.api.api_request")
    mock_api_request.return_value.json.return_value = company_input_data

    assert Company.objects.count() == 0

    output = company_list_search({"search_term": "hello world"})

    assert output["total_matches"] == 2
    assert output["total_returned"] == 2
    assert output["page_size"] == 0
    assert output["page_number"] == 1
    assert len(output["results"]) == 2
    assert Company.objects.count() == 0

    assert mock_api_request.call_args[0] == ("POST", "/v1/search/companyList")
    assert mock_api_request.call_args[1]["json"] == {"searchTerm": "hello world"}

    for input_data, expected in zip(
        company_input_data["searchCandidates"], output["results"]
    ):
        assert extract_company_data(input_data) == expected


@pytest.mark.django_db
def test_company_list_search_v2(
    mocker, company_list_v2_api_response_json, company_list_v2_expected_data_json
):
    company_input_data = json.loads(company_list_v2_api_response_json)
    expected_company_data = json.loads(company_list_v2_expected_data_json)

    mock_api_request = mocker.patch("dnb_direct_plus.api.api_request")
    mock_api_request.return_value.json.return_value = company_input_data

    assert Company.objects.count() == 0

    output = company_list_search_v2(
        {
            "duns_number": "804735132",
            "address_country": "US",
            "search_term": "company name",
        }
    )

    assert len(output["results"]) == 1
    assert Company.objects.count() == 0

    for expected_data, result_data in zip(expected_company_data, output["results"]):
        assert extract_company_data(expected_data) == result_data


@pytest.mark.django_db
def test_company_list_search_detail_query_company_data_is_saved(
    mocker, company_list_api_response_json
):
    company_input_data = json.loads(company_list_api_response_json)

    company_input_data["searchCandidates"].pop()
    company_input_data["candidatesReturnedQuantity"] = 1
    company_input_data["candidatesMatchedQuantity"] = 1

    mock_api_request = mocker.patch("dnb_direct_plus.api.api_request")
    mock_api_request.return_value.json.return_value = company_input_data

    assert Company.objects.count() == 0

    output = company_list_search(
        {
            "duns_number": "hello world",
        },
        update_local=True,
    )

    assert Company.objects.count() == 1

    company = Company.objects.first()

    assert company.duns_number == output["results"][0]["duns_number"]
    assert company.monitoring_status == MonitoringStatusChoices.pending.name


@pytest.mark.django_db
def test_company_list_search_v2_detail_query_company_data_is_saved(
    mocker, company_list_v2_api_response_json, data_duns_api_response_json
):
    """
    Test to ensure that only up to date data is saved for v2
    company_list_v2_api_response_json contains the search request with old data
    while data_duns_api_response_json contains the up to date data for that company
    """
    company_input_data = json.loads(company_list_v2_api_response_json)
    up_to_date_company_data = json.loads(data_duns_api_response_json)

    class ApiRequestFake:
        def __init__(self, *posargs, **kwargs):
            self.posargs = posargs
            self.kwargs = kwargs

            if self.posargs == ("GET", "/v1/match/cleanseMatch"):
                assert self.kwargs["params"] == {
                    "duns": "804735132",
                    "countryISOAlpha2Code": "US",
                }

                self.json_data = company_input_data
            elif self.posargs == ("GET", "/v1/data/duns/804735132"):
                self.json_data = up_to_date_company_data
            else:
                raise AssertionError(
                    f"Unexpected API request posargs={posargs} kwargs={kwargs}"
                )

        def json(self):
            return self.json_data

    mock_api_request = mocker.patch(
        "dnb_direct_plus.api.api_request", new=ApiRequestFake
    )

    assert Company.objects.count() == 0

    output = company_list_search_v2(
        {
            "duns_number": "804735132",
            "address_country": "US",
        },
        update_local=True,
    )

    assert Company.objects.count() == 1

    company = Company.objects.first()

    assert (
        company.address_country.iso_alpha2
        == up_to_date_company_data["organization"]["primaryAddress"]["addressCountry"][
            "isoAlpha2Code"
        ]
    )
    assert company.duns_number == output["results"][0]["duns_number"]
    assert company.monitoring_status == MonitoringStatusChoices.pending.name


class ApiHierarchyRequestJsonFake:
    def __init__(self, json_data):
        self.json_data = json_data

    def json(self):
        return self.json_data


@pytest.mark.django_db
def test_company_hierarchy_single_list_search(
    mocker, company_hierarchy_api_response_json
):
    company_hierarchy_data = json.loads(company_hierarchy_api_response_json)
    mock_api_request = mocker.patch("dnb_direct_plus.api.api_request")

    mock_api_request.return_value.json.return_value = company_hierarchy_data

    output = company_hierarchy_list_search({"duns_number": "111111111"})

    assert output["global_ultimate_duns"] == "111111111"
    assert output["global_ultimate_family_tree_members_count"] == 3
    assert output["branches_excluded_members_count"] == 2
    assert output["family_tree_members"][0]["duns"] == "111111111"
    assert output["family_tree_members"][1]["duns"] == "222222222"
    assert output["family_tree_members"][2]["duns"] == "333333333"


@pytest.mark.django_db
def test_company_hierarchy_paginated_list_search(
    mocker,
    company_hierarchy_first_page_api_response_json,
    company_hierarchy_last_page_api_response_json,
):
    company_hierarchy_first_page_data = json.loads(
        company_hierarchy_first_page_api_response_json
    )
    company_hierarchy_last_page_data = json.loads(
        company_hierarchy_last_page_api_response_json
    )

    mock_api_request = mocker.patch("dnb_direct_plus.api.api_request")
    mock_api_request.side_effect = [
        ApiHierarchyRequestJsonFake(json_data=company_hierarchy_first_page_data),
        ApiHierarchyRequestJsonFake(json_data=company_hierarchy_last_page_data),
    ]

    output = company_hierarchy_list_search({"duns_number": "111111111"})

    assert output["global_ultimate_duns"] == "444444444"
    assert output["global_ultimate_family_tree_members_count"] == 2
    assert output["branches_excluded_members_count"] == 1
    assert output["family_tree_members"][0]["duns"] == "444444444"
    assert output["family_tree_members"][1]["duns"] == "555555555"


def test_company_hierarchy_count_returns_value(mocker):
    mock_api_request = mocker.patch("dnb_direct_plus.api.api_request")
    mock_api_request.side_effect = (
        ApiHierarchyRequestJsonFake(
            json_data={"globalUltimateFamilyTreeMembersCount": 15}
        ),
    )
    count = company_hierarchy_count({"duns_number": "111111111"})
    assert count == 15


class MockHTTPErrorResponse:
    """Mock response object for HTTPError testing."""

    def __init__(self, status_code, response_json):
        self.status_code = status_code
        self.response_json = response_json

    def json(self):
        return self.response_json


def test_company_hierarchy_api_request_success_no_logging(mocker, caplog):
    """Test that successful requests don't generate any log entries."""
    expected_data = {
        "globalUltimateFamilyTreeMembersCount": 10,
        "familyTreeMembers": [],
    }
    mock_api_request = mocker.patch("dnb_direct_plus.api.api_request")
    mock_api_request.side_effect = [ApiHierarchyRequestJsonFake(expected_data)]

    test_url = "v1/familyTree/"

    with caplog.at_level("INFO"):
        result = company_hierarchy_api_request(test_url)

    assert result == expected_data
    mock_api_request.assert_called_once_with("GET", test_url)

    assert len(caplog.records) == 0


def test_company_hierarchy_api_request_404_logging(mocker, caplog):
    """Test that 404 errors are not raised and logged at INFO level with D&B error details."""
    error_code = "000404"
    error_message = "Unable to find requested company"
    mock_response = MockHTTPErrorResponse(
        status_code=404,
        response_json={
            "error": {
                "errorCode": error_code,
                "errorMessage": error_message,
            }
        },
    )
    http_error = HTTPError()
    http_error.response = mock_response

    mock_api_request = mocker.patch("dnb_direct_plus.api.api_request")
    mock_api_request.side_effect = http_error

    test_url = "v1/familyTree/"

    with caplog.at_level("INFO"):
        result = company_hierarchy_api_request(test_url)

    assert result == {}
    mock_api_request.assert_called_once_with("GET", test_url)

    assert len(caplog.records) == 1
    log_record = caplog.records[0]
    assert log_record.levelname == "INFO"
    assert f"Company hierarchy not found - {test_url} - " in log_record.message
    assert f"D&B error {error_code}: {error_message}" in log_record.message


def test_company_hierarchy_api_request_non_404_logging(mocker, caplog):
    """Test that non-404 errors are raised and logged at ERROR level with D&B error details."""
    error_code = "000400"
    error_message = "Bad request"
    mock_response = MockHTTPErrorResponse(
        status_code=400,
        response_json={
            "error": {
                "errorCode": error_code,
                "errorMessage": error_message,
            }
        },
    )
    http_error = HTTPError()
    http_error.response = mock_response

    mock_api_request = mocker.patch("dnb_direct_plus.api.api_request")
    mock_api_request.side_effect = http_error

    test_url = "v1/familyTree/"

    with (
        pytest.raises(HTTPError),
        caplog.at_level("ERROR"),
    ):
        company_hierarchy_api_request(test_url)

    mock_api_request.assert_called_once_with("GET", test_url)

    assert len(caplog.records) == 1
    log_record = caplog.records[0]
    assert log_record.levelname == "ERROR"
    assert f"D&B error {error_code}: {error_message}" in log_record.message
