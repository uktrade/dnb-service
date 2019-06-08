from django.forms import Field, ValidationError
from django.utils.translation import ugettext as _

from .models import Country


class IsoAlpha2CountryField(Field):
    """A custom django field that accepts an iso2 alpha code and looks up the associated `company.Country` instance.
    """

    default_error_messages = {
        'required': _('This field is required.'),
        'no_match': _('No matching Country with iso alpha 2 code: {invalid_code}.'),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self, field):
        if not field and not self.required:
            return field

        if not field and self.required:
            raise ValidationError(self.error_messages['required'])

        try:
            return Country.objects.get(iso_alpha2=field)
        except Country.DoesNotExist:
            raise ValidationError(self.error_messages['no_match'].format(
                invalid_code=field
            ))
