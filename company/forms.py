from django.forms import ModelForm

from .fields import IsoAlpha2CountryField
from .models import Company, RegistrationNumber


class CompanyValidationForm(ModelForm):
    """A form used to validate incoming data"""

    address_country = IsoAlpha2CountryField(required=True)
    registered_address_country = IsoAlpha2CountryField(required=False)

    class Meta:
        model = Company
        exclude = ('created', 'last_updated', )


class RegistrationNumberValidationForm(ModelForm):
    """A form used to validate incoming data"""

    class Meta:
        model = RegistrationNumber
        exclude = ('company',)
