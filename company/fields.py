from django.forms import Field, ValidationError

from .models import Country


class IsoAlpha2CountryField(Field):
    """A custom django field that accepts an iso2 alpha code and looks up the associated `company.Country` instance.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self, field):
        if not field and not self.required:
            return field

        if not field and self.required:
            raise ValidationError('This field is required.')

        try:
            return Country.objects.get(iso_alpha2=field)
        except Country.DoesNotExist:
            raise ValidationError(f'No matching Country with iso alpha 2 code {field}')
