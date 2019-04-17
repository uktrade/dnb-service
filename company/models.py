from company.constants import LastUpdatedSource, LegalStatusChoices, RegistrationNumberChoices

from django.contrib.postgres.fields import ArrayField
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Country(models.Model):
    name = models.CharField(
        max_length=255,
    )

    iso_alpha2 = models.CharField(
        max_length=2,
        help_text=_('ISO 2 digit alphanumeric country code'),
    )

    iso_alpha3 = models.CharField(
        max_length=3,
        help_text=_('ISO 3 digital alphanumeric country code'),
    )

    iso_numeric = models.PositiveIntegerField(
        help_text=_('ISO 3 digit numeric country code'),
    )

    class Meta:
        verbose_name_plural = 'Countries'
        ordering = ('name',)

    def __str__(self):
        return self.name


class RegistrationNumber(models.Model):
    """A model for recording company registration numbers such as the
    companies House number and VAT registration number """

    registration_type = models.CharField(
        max_length=100,
        choices=RegistrationNumberChoices.list()
    )

    registration_number = models.CharField(
        max_length=50,
        blank=False,
    )

    def __str__(self):
        return self.registration_number


class Company(models.Model):
    """The main DNB company model"""

    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    last_updated_source = models.PositiveIntegerField(
        choices=LastUpdatedSource.list()
    )

    duns_number = models.CharField(
        _('Duns number'),
        max_length=9,
        db_index=True,
        validators=[RegexValidator(
            regex=r'^\d{9}$', message=_('Field should contain 9 numbers only'), code='invalid')]
    )

    primary_name = models.CharField(
        _('Primary name'),
        max_length=90,
    )

    trading_names = ArrayField(
        models.CharField(max_length=255),
        blank=True,
        default=list,
    )

    address_line_1 = models.CharField(
        _('Street address'),
        blank=True,
        max_length=64,
    )

    address_line_2 = models.CharField(
        _('Street address 2'),
        blank=True,
        max_length=64,
    )

    address_town = models.CharField(
        _('City'),
        blank=True,
        max_length=30,
    )

    address_county = models.CharField(
        _('State'),
        blank=True,
        max_length=30,
    )

    address_country = models.ForeignKey(
        Country,
        _('Country'),
        null=False,
        related_name='+',
    )

    address_postcode = models.CharField(
        _('Postal code'),
        blank=True,
        max_length=9,
    )

    registered_address_line_1 = models.CharField(
        _('Street address'),
        blank=True,
        max_length=64,
    )

    registered_address_line_2 = models.CharField(
        _('Street address 2'),
        blank=True,
        max_length=64,
    )

    registered_address_town = models.CharField(
        _('City'),
        blank=True,
        max_length=30,
    )

    registered_address_county = models.CharField(
        _('State'),
        blank=True,
        max_length=30,
    )

    registered_address_country = models.ForeignKey(
        Country,
        _('Country'),
        blank=True,
        null=True,
        related_name='+',
    )

    registered_address_postcode = models.CharField(
        _('Postal code'),
        blank=True,
        max_length=9,
    )

    registration_numbers = models.ManyToManyField(RegistrationNumber, blank=True)

    line_of_business = models.CharField(
        _('Line of business'),
        max_length=41,
    )

    is_out_of_business = models.BooleanField(
        _('Is out of business?'),
    )

    year_started = models.PositiveIntegerField(
        _('Year started'),
    )

    global_ultimate_duns_number = models.CharField(
        _('Glogal ultimate duns number'),
        max_length=9,
        blank=True,
        validators=[RegexValidator(
            regex=r'^\d{9}$', message=_('Field should contain 9 numbers only'), code='invalid')],
        db_index=True,
    )

    employee_number = models.PositiveIntegerField(
        _('Employee number'),
        blank=True,
        null=True,
    )

    is_employees_number_estimated = models.BooleanField(
        _('Is employee number estimated?'),
        blank=True,
        null=True,
    )

    annual_sales = models.FloatField(
        _('Annual sales'),
        help_text=_('Annual sales in US dollars'),
        blank=True,
        null=True,
    )

    is_annual_sales_estimated = models.BooleanField(
        _('Is annual sales estimated?'),
        blank=True,
        null=True,
    )

    legal_status = models.CharField(
        _('Legal status'),
        max_length=3,
    )

    status_code = models.PositiveIntegerField(
        _('Status code'),
        choices=LegalStatusChoices.list(),
    )

    class Meta:
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.primary_name
