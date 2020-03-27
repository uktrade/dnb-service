import json

import pytest

from ..api import company_list_search
from ..mapping import extract_company_data
from company.constants import MonitoringStatusChoices
from company.models import Company


pytestmark = pytest.mark.django_db


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

    assert mock_api_request.call_args[1]['json'] == {
        'searchTerm': 'hello world'
    }

    for input_data, expected in zip(company_input_data['searchCandidates'], output['results']):
        assert extract_company_data(input_data) == expected


@pytest.mark.parametrize('enable_monitoring,monitoring_status', [
    (True, MonitoringStatusChoices.pending.name),
    (False, MonitoringStatusChoices.not_enabled.name),
])
def test_company_list_search_detail_query_company_data_is_saved(mocker,
                                                                company_list_api_response_json,
                                                                enable_monitoring, monitoring_status):

    company_input_data = json.loads(company_list_api_response_json)

    company_input_data['searchCandidates'].pop()
    company_input_data['candidatesReturnedQuantity'] = 1
    company_input_data['candidatesMatchedQuantity'] = 1

    mock_api_request = mocker.patch('dnb_direct_plus.api.api_request')
    mock_api_request.return_value.json.return_value = company_input_data

    assert Company.objects.count() == 0

    output = company_list_search(
        {'duns_number': 'hello world',}, update_local=True, enable_monitoring=enable_monitoring)

    assert Company.objects.count() == 1

    company = Company.objects.first()

    assert company.duns_number == output['results'][0]['duns_number']

    assert company.monitoring_status == monitoring_status
