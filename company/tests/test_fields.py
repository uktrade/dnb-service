import pytest
from django.forms import ValidationError

from ..fields import IsoAlpha2CountryField
from ..models import Country


@pytest.mark.django_db
class TestIso2AlphaCountryField:
    @pytest.mark.parametrize('field_required,input_value', [
        (True, 'GB'),
        (False, 'US'),
    ])
    def test_with_valid_data(self, field_required, input_value):
        field = IsoAlpha2CountryField(required=field_required)
        assert field.clean(input_value) == Country.objects.get(iso_alpha2=input_value)

    def test_empty(self):
        field = IsoAlpha2CountryField(required=False)

        assert field.clean('') == ''

    @pytest.mark.parametrize('field_required,input_value', [
        (
            True,
            '',
        ),
        (
            True,
            'xyz',
        ),
        (
            False,
            'xyz',
        ),
    ])
    def test_failure(self, field_required, input_value):
        field = IsoAlpha2CountryField(required=field_required)

        with pytest.raises(ValidationError):
            field.clean(input_value)
