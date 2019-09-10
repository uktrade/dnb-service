import pytest

from api.serialisers import CompanySearchInputSerialiser
from rest_framework.exceptions import ErrorDetail


@pytest.mark.parametrize('input, data, errors', [
    # at least one standalone argument is required - duns_number or search_term
    (
        {},
        {},
        {'non_field_errors': [ErrorDetail(string='At least one standalone field required.', code='invalid')]},
    ),
    # valid input
    (
        {
            'search_term': 'hello'
        },
        {'search_term': 'hello', 'page_size': 1, 'page_number': 1},
        {}
    )
])
def test_company_search_input_serialiser(input, data, errors):
    serialiser = CompanySearchInputSerialiser(data=input)

    is_valid = not errors

    assert serialiser.is_valid() == is_valid
    assert serialiser.data == data
    assert serialiser.errors == errors
