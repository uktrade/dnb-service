import pytest

from ..constants import LegalStatusChoices
from ..forms import CompanyValidationForm


@pytest.fixture()
def input_data(request):

    test_data = {
        'duns_number': '123456789',
        'primary_name': 'widgets pty',
        'address_country': 'GB',
        'year_started': '1999',
        'legal_status': LegalStatusChoices.corporation.name,
        'is_out_of_business': False,
    }

    test_data.update(request.param)

    return test_data


@pytest.mark.parametrize(
    'input_data,errors',
    [
        (
            # the default input_data fixture should validate
            {},
            {}
        ),
        (
            {
                'duns_number': 'xxxxx'
            },
            {
                'duns_number': ['Field should contain 9 numbers only'],
            },
        ),
        (
            {
                'last_updated_source': 'xxx',
            },
            {
                'last_updated_source': ['Select a valid choice. xxx is not one of the available choices.'],
            },
        ),
        (
            {
                'primary_name': '',
            },
            {
                'primary_name': ['This field is required.'],
            },
        ),
        (
            {
                'year_started': '',
            },
            {
                'year_started': ['This field is required.'],
            },
        ),
        (
            {
                'legal_status': '',
            },
            {
                'legal_status': ['This field is required.'],
            },
        ),
        (
            {
                'global_ultimate_duns_number': 'xxxxx',
            },
            {
                'global_ultimate_duns_number': ['Field should contain 9 numbers only'],
            },
        ),
        (
            {
                'address_country': '',
            },
            {
                'address_country': ['This field is required.'],
            },
        ),
        (
            {
                'address_country': 'XY',
            },
            {
                'address_country': ['No matching Country with iso alpha 2 code: XY.'],
            },
        ),
    ],
    indirect=['input_data'],
)
@pytest.mark.django_db
@pytest.mark.skip()
def test_duns_number(input_data, errors):
    form = CompanyValidationForm(input_data)

    is_form_valid = not errors

    assert form.is_valid() == is_form_valid
    assert form.errors == errors
