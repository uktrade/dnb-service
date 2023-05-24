import json

import pytest

from ..api import company_list_search, company_list_search_v2, company_hierarchy_list_search, company_hierarchy_list_next_request
from ..mapping import extract_company_data
from company.constants import MonitoringStatusChoices
from company.models import Company


@pytest.mark.django_db
def test_company_list_search(mocker, company_list_api_response_json):

    company_input_data = json.loads(company_list_api_response_json)

    mock_api_request = mocker.patch('dnb_direct_plus.api.api_request')
    mock_api_request.return_value.json.return_value = company_input_data

    assert Company.objects.count() == 0

    output = company_list_search({
        'search_term': 'hello world'
    })

    assert output['total_matches'] == 2
    assert output['total_returned'] == 2
    assert output['page_size'] == 0
    assert output['page_number'] == 1
    assert len(output['results']) == 2
    assert Company.objects.count() == 0

    assert mock_api_request.call_args[0] == ('POST', '/v1/search/companyList')
    assert mock_api_request.call_args[1]['json'] == {
        'searchTerm': 'hello world'
    }

    for input_data, expected in zip(company_input_data['searchCandidates'], output['results']):
        assert extract_company_data(input_data) == expected

@pytest.mark.django_db
def test_company_list_search_v2(mocker, company_list_v2_api_response_json, company_list_v2_expected_data_json):
    company_input_data = json.loads(company_list_v2_api_response_json)
    expected_company_data = json.loads(company_list_v2_expected_data_json)

    mock_api_request = mocker.patch('dnb_direct_plus.api.api_request')
    mock_api_request.return_value.json.return_value = company_input_data

    assert Company.objects.count() == 0

    output = company_list_search_v2({
        'duns_number': '804735132',
        'address_country': 'US',
        'search_term': 'company name'
    })

    assert len(output['results']) == 1
    assert Company.objects.count() == 0

    for expected_data, result_data in zip(expected_company_data, output['results']):
        assert extract_company_data(expected_data) == result_data


@pytest.mark.django_db
def test_company_list_search_detail_query_company_data_is_saved(mocker, company_list_api_response_json):

    company_input_data = json.loads(company_list_api_response_json)

    company_input_data['searchCandidates'].pop()
    company_input_data['candidatesReturnedQuantity'] = 1
    company_input_data['candidatesMatchedQuantity'] = 1

    mock_api_request = mocker.patch('dnb_direct_plus.api.api_request')
    mock_api_request.return_value.json.return_value = company_input_data

    assert Company.objects.count() == 0

    output = company_list_search({'duns_number': 'hello world',}, update_local=True)

    assert Company.objects.count() == 1

    company = Company.objects.first()

    assert company.duns_number == output['results'][0]['duns_number']
    assert company.monitoring_status == MonitoringStatusChoices.pending.name

@pytest.mark.django_db
def test_company_list_search_v2_detail_query_company_data_is_saved(mocker, company_list_v2_api_response_json, data_duns_api_response_json):
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

            if self.posargs == ('GET', '/v1/match/cleanseMatch'):
                assert self.kwargs['params'] == {
                    'duns': '804735132',
                    'countryISOAlpha2Code': 'US'
                }

                self.json_data = company_input_data
            elif self.posargs == ('GET', '/v1/data/duns/804735132'):
                self.json_data = up_to_date_company_data
            else:
                raise AssertionError(f'Unexpected API request posargs={posargs} kwargs={kwargs}')

        def json(self):
            return self.json_data

    mock_api_request = mocker.patch('dnb_direct_plus.api.api_request', new=ApiRequestFake)

    assert Company.objects.count() == 0

    output = company_list_search_v2({
        'duns_number': '804735132',
        'address_country': 'US',
    }, update_local=True)

    assert Company.objects.count() == 1

    company = Company.objects.first()

    assert company.address_country.iso_alpha2 == up_to_date_company_data['organization']['primaryAddress']['addressCountry']['isoAlpha2Code']
    assert company.duns_number == output['results'][0]['duns_number']
    assert company.monitoring_status == MonitoringStatusChoices.pending.name

@pytest.mark.django_db
def test_company_hierarchy_single_list_search(mocker, company_hierarchy_api_response_json):

    company_hierarchy_data = json.loads(company_hierarchy_api_response_json)
    mock_api_request = mocker.patch('dnb_direct_plus.api.api_request')

    print(mock_api_request)

    mock_api_request.return_value.json.return_value = company_hierarchy_data

    print(mock_api_request.return_value)
    print(mock_api_request.return_value.json)
    print(mock_api_request.return_value.json.return_value)

    output = company_hierarchy_list_search({
        'duns_number': '111111111'
    })

    assert output['results']['global_ultimate_duns'] == '111111111'
    assert output['results']['global_ultimate_family_tree_members_count'] == 3
    assert output['results']['branches_excluded_members_count'] == 2
    assert output['results']['family_tree_members'][0]['duns'] == '111111111'
    assert output['results']['family_tree_members'][1]['duns'] == '222222222'
    assert output['results']['family_tree_members'][2]['duns'] == '333333333'

@pytest.mark.django_db
def test_company_hierarchy_paginated_list_search(mocker, company_hierarchy_first_page_api_response_json, company_hierarchy_last_page_api_response_json):


    class ApiHierarchyRequestFake:
        def __init__(self, json_data):
            self.json_data = json_data

        def json(self):
            return self.json_data

    company_hierarchy_first_page_data = json.loads(company_hierarchy_first_page_api_response_json)
    company_hierarchy_last_page_data = json.loads(company_hierarchy_last_page_api_response_json)

    mock_api_request = mocker.patch('dnb_direct_plus.api.api_request')
    mock_api_request.side_effect = [ApiHierarchyRequestFake(json_data=company_hierarchy_first_page_data), ApiHierarchyRequestFake(json_data=company_hierarchy_last_page_data)]

    output = company_hierarchy_list_search({
        'duns_number': '111111111'
    })


    print('oooooooooooooooooo', output)
    
    assert output['results']['global_ultimate_duns'] == '444444444'
    assert output['results']['global_ultimate_family_tree_members_count'] == 2
    assert output['results']['branches_excluded_members_count'] == 1
    assert output['results']['family_tree_members'][0]['duns'] == '444444444'
    assert output['results']['family_tree_members'][1]['duns'] == '555555555'
    