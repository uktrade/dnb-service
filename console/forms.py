from django import forms

from govuk_forms.forms import GOVUKForm
from govuk_forms import widgets

from dnb_worldbase.constants import DNB_COUNTRY_CODE_MAPPING

from .constants import ISO_COUNTRY_CHOICES

COUNTRIES = set(DNB_COUNTRY_CODE_MAPPING.values())

DEFAULT_PAGE_SIZE = 10

PAGE_SIZE_CHOICES = (
    (10, '10'),
    (20, '20'),
    (30, '30'),
    (40, '40'),
    (50, '50'),
)


class SearchForm(GOVUKForm):
    searchTerm = forms.CharField(
        label='Company name',
        help_text='Search companies primary or trading names',
        required=True,
        widget=widgets.TextInput(),
    )
    countryISOAlpha2Code = forms.ChoiceField(
        label='Country',
        required=False,
        widget=widgets.Select(),
        choices=ISO_COUNTRY_CHOICES,
        initial='GB',
    )
    isOutOfBusiness = forms.BooleanField(
        label='Is out of business?',
        help_text='Return companies that are out of business',
        initial=False,
        required=False,
        widget=widgets.CheckboxInput(),
    )
    pageSize = forms.TypedChoiceField(
        label='Number of results',
        initial=10,
        widget=widgets.Select(),
        choices=PAGE_SIZE_CHOICES,
        coerce=int,
    )
