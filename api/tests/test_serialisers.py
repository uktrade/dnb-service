import pytest

from rest_framework.exceptions import ErrorDetail

from api.serialisers import CompanySearchInputSerialiser, CompanySearchV2InputSerialiser, CompanyHierarchySearchInputSerialiser


@pytest.mark.parametrize('input, data, errors', [
    # at least one standalone argument is required - duns_number or search_term
    (
        {},
        {},
        {'non_field_errors': [
            ErrorDetail(
                string="At least one standalone field required: ['duns_number', 'search_term', "
                       "'primary_name', 'registration_numbers'].",
                code='invalid'
            )
        ]},
    ),
    # valid input
    (
        {
            'search_term': 'hello'
        },
        {'search_term': 'hello', 'page_size': 10, 'page_number': 1},
        {}
    )
])
def test_company_search_input_serialiser(input, data, errors):
    serialiser = CompanySearchInputSerialiser(data=input)

    is_valid = not errors

    assert serialiser.is_valid() == is_valid
    assert serialiser.data == data
    assert serialiser.errors == errors

@pytest.mark.parametrize('input, data, errors', [
    # at least one standalone argument is required - duns_number or search_term
    (
        {},
        {},
        {'non_field_errors': [
            ErrorDetail(
                string="At least one standalone field required: ['duns_number', 'search_term'].",
                code='invalid'
            )
        ]},
    ),
    # valid input
    (
        {
            'search_term': 'hello'
        },
        {
            'search_term': 'hello'
        },
        {}
    )
])
def test_company_search_v2_input_serialiser(input, data, errors):
    serialiser = CompanySearchV2InputSerialiser(data=input)

    is_valid = not errors

    assert serialiser.is_valid() == is_valid
    assert serialiser.data == data
    assert serialiser.errors == errors

@pytest.mark.parametrize('input, data, errors', [
    # at least one standalone argument is required - duns_number
    (
        {},
        {},
        {'non_field_errors': [
            ErrorDetail(
                string="At least one standalone field required: ['duns_number'].",
                code='invalid'
            )
        ]},
    ),
    # valid input
    (
        {
            'duns_number': '111111111'
        },
        {
            'duns_number': '111111111'
        },
        {}
    )
])
def test_company_hierarchy_input_serialiser(input, data, errors):
    serialiser = CompanyHierarchySearchInputSerialiser(data=input)

    is_valid = not errors

    assert serialiser.is_valid() == is_valid
    assert serialiser.data == data
    assert serialiser.errors == errors
