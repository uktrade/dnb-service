from django.core.validators import RegexValidator
from django.db import models

from django.utils.translation import ugettext_lazy as _


class Company(models.Model):
    LAST_UPDATED_API = 1
    LAST_UPDATED_FILE = 2

    LAST_UPDATED_SOURCE_CHOICES = (
        (LAST_UPDATED_FILE, _('File')),
        (LAST_UPDATED_API, _('API'))
    )

    STATUS_CODE_CHOICES = (
        (0, _('Single location')),
        (1, _('Headquarter')),
        (2, _('Branch')),
        (4, _('Division')),
    )

    LEGAL_STATUS_CHOICES = (
        (0, _('Not available')),
        (3, _('Corporation')),
        (8, _('Joint venture')),
        (12, _('Partnership')),
        (13, _('Proprietorship')),
        (120, _('Foreign; Company'))
    )

    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    last_updated_source = models.PositiveIntegerField(
        choices=LAST_UPDATED_SOURCE_CHOICES
    )

    duns_number = models.CharField(
        _('Duns number'),
        max_length=9,
        db_index=True,
        validators=[RegexValidator(regex=r'^\d{9}$', message=_('Field should contain 9 numbers only'), code='invalid')]
    )

    business_name = models.CharField(
        _('Business name'),
        max_length=90,
    )
    secondary_name = models.CharField(

        _('Secondary name'),
        max_length=90, blank=True, null=True,
    )

    street_address = models.CharField(
        _('Street address'),
        max_length=64,
    )

    street_address2 = models.CharField(
        _('Street address 2'),
        max_length=64,
    )

    city = models.CharField(
        _('City'),
        max_length=30,
    )

    state = models.CharField(
        _('State'),
        max_length=30,
    )

    country_name = models.CharField(
        _('Country name'),
        max_length=20,
    )

    country_code = models.CharField(
        _('Country code'),
        max_length=3,
        help_text=_('3 digit ISO country code'),
    )

    postal_code = models.CharField(
        _('Postal code'),
        max_length=9,
    )

    national_id_number = models.CharField(
        _('National ID number'),
        max_length=16,
    )

    national_id_code_type = models.CharField(
        _('National ID code type'),
        max_length=5,
    )

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
        max_length=9, db_index=True,
    )

    employee_number = models.PositiveIntegerField(
        _('Employee number'),
    )
    is_employees_number_estimated = models.BooleanField(
        _('Is employee number estimated?'),
    )

    annual_sales = models.FloatField(
        _('Annual sales'),
        help_text=_('Annual sales in US dollars'),
    )

    is_annual_sales_estimated = models.BooleanField(
        _('Is annual sales estimated?'),
    )

    legal_status = models.CharField(
        _('Legal status'),
        max_length=3,
    )

    status_code = models.PositiveIntegerField(
        _('Status code'),
        choices=STATUS_CODE_CHOICES,
    )

    @property
    def uk_company_number(self):
        if self.national_id_code_type == '00012':
            return self.national_id_number
        else:
            return None

    class Meta:
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.business_name
