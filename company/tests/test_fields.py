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

    @pytest.mark.parametrize('input_value', [
        '',
        None,
    ])
    def test_empty(self, input_value):
        field = IsoAlpha2CountryField(required=False)
        assert field.clean(input_value) is None

    @pytest.mark.parametrize('field_required,input_value,exception_text', [
        (
            True,
            '',
            'This field is required.',
        ),
        (
            True,
            'xyz',
            'No matching Country with iso alpha 2 code: xyz.',
        ),
        (
            False,
            'xyz',
            'No matching Country with iso alpha 2 code: xyz.',
        ),
    ])
    def test_failure(self, field_required, input_value, exception_text):
        field = IsoAlpha2CountryField(required=field_required)

        with pytest.raises(ValidationError) as ex:
            field.clean(input_value)

        assert ex.value.message == exception_text
