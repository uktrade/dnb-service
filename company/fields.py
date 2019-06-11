from django.forms import Field, ValidationError
from django.utils.translation import ugettext as _

from .models import Country


class IsoAlpha2CountryField(Field):
    """A custom django field that accepts an iso2 alpha code and looks up the associated `company.Country` instance.
    """

    default_error_messages = {
        'no_match': _('No matching Country with iso alpha 2 code: {invalid_code}.'),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self, field):
        cleaned_value = super().clean(field)

        if not cleaned_value and not self.required:
            return None

        try:
            return Country.objects.get(iso_alpha2=cleaned_value)
        except Country.DoesNotExist:
            raise ValidationError(self.error_messages['no_match'].format(
                invalid_code=cleaned_value
            ))
