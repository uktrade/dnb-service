import json

from ..api import company_list_search
from ..mapping import extract_company_data


def test_company_list_search(mocker, company_list_api_response_json):

    company_input_data = json.loads(company_list_api_response_json)

    mock_api_request = mocker.patch('dnb_direct_plus.api.api_request')
    mock_api_request.return_value.json.return_value = company_input_data

    output = company_list_search({
        'search_term': 'hello world'
    })

    assert output['total_matches'] == 2
    assert output['total_returned'] == 2
    assert output['page_size'] == 0
    assert output['page_number'] == 1
    assert len(output['results']) == 2

    assert mock_api_request.call_args[1]['json'] == {
        'searchTerm': 'hello world'
    }

    for input_data, expected in zip(company_input_data['searchCandidates'], output['results']):
        assert extract_company_data(input_data) == expected
