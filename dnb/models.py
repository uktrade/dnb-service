from django.db import models
from django.core.validators import RegexValidator

from django.utils.translation import ugettext_lazy as _


class Company(models.Model):
    LAST_UPDATED_API = 1
    LAST_UPDATED_FILE = 2

    LAST_UPDATED_SOURCE_CHOICES = (
        (LAST_UPDATED_FILE, 'File'),
        (LAST_UPDATED_API, 'API')
    )

    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    last_updated_source = models.PositiveIntegerField(
        choices=LAST_UPDATED_SOURCE_CHOICES
    )

    duns_number = models.CharField(
        max_length=9,
        db_index=True,
        validators=[RegexValidator(regex='^\d{9}$', message='Field should contain 9 numbers only', code='invalid')]
    )

    business_name = models.CharField(
        max_length=90
    )
    secondary_name = models.CharField(
        max_length=90, blank=True, null=True
    )

    street_address = models.CharField(
        max_length=64
    )

    street_address2 = models.CharField(
        max_length=64
    )

    city = models.CharField(
        max_length=30
    )

    state = models.CharField(
        max_length=30
    )

    country_name = models.CharField(
        max_length=20
    )

    country_code = models.CharField(
        max_length=3
    )

    postal_code = models.CharField(
        max_length=9
    )

    national_id_number = models.CharField(
        max_length=16
    )

    national_id_code_type = models.CharField(
        max_length=255
    )

    line_of_business = models.CharField(
        max_length=41
    )

    is_out_of_business = models.BooleanField()

    year_started = models.PositiveIntegerField()

    global_ultimate_duns_number = models.CharField(
        max_length=9, db_index=True
    )

    employee_number = models.PositiveIntegerField()
    is_employees_number_estimated = models.BooleanField()

    annual_sales = models.FloatField(
        help_text=_('Annual sales in US dollars')
    )

    is_annual_sales_estimated = models.BooleanField()

    legal_status = models.CharField(max_length=255)
    status_code = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = 'Companies'
