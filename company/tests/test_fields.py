import pytest
from django.forms import ValidationError

from ..fields import IsoAlpha2CountryField
from ..models import Country


@pytest.mark.django_db
class TestIso2AlphaCountryField:
    @pytest.mark.parametrize('test_input,expected', [
        (
            {
                'params': {'required': True},
                'value': 'GB',
            },
            'GB',
        ),
        (
            {
                'params': {'required': False},
                'value': 'US',
            },
            'US',
        ),
    ])
    def test_with_valid_data(self, test_input, expected):
        field = IsoAlpha2CountryField(**test_input['params'])
        assert field.clean(test_input['value']) == Country.objects.get(iso_alpha2=expected)

    def test_empty(self):
        field = IsoAlpha2CountryField(required=False)

        assert field.clean('') == ''

    @pytest.mark.parametrize('test_input,exception', [
        (
            {
                'params': {'required': True},
                'value': '',
            },
            ValidationError,
        ),
        (
            {
                'params': {'required': True},
                'value': 'xyz',
            },
            ValidationError,
        ),
        (
            {
                'params': {'required': False},
                'value': 'xyz',
            },
            ValidationError,
        ),
    ])
    def test_failure(self, test_input, exception):
        field = IsoAlpha2CountryField(**test_input['params'])

        with pytest.raises(exception):
            field.clean(test_input['value'])
