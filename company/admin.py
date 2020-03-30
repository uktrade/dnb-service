from django.contrib import admin

from .models import (
    ChangeRequest,
    Company,
    Country,
    IndustryCode,
    InvestigationRequest,
    PrimaryIndustryCode,
    RegistrationNumber,
)


class RegistrationNumberInline(admin.TabularInline):
    model = RegistrationNumber


class IndustryCodeInline(admin.TabularInline):
    model = IndustryCode


class PrimaryIndustryCodeInline(admin.TabularInline):
    model = PrimaryIndustryCode


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('duns_number', 'primary_name', 'is_out_of_business', 'created', 'last_updated')
    list_filter = ('is_out_of_business', 'is_employees_number_estimated', 'is_annual_sales_estimated')
    search_fields = ('duns_number', 'primary_name')

    inlines = [
        RegistrationNumberInline,
        IndustryCodeInline,
        PrimaryIndustryCodeInline,
    ]


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'iso_alpha2', 'iso_alpha3', 'iso_numeric')


@admin.register(ChangeRequest)
class ChangeRequestAdmin(admin.ModelAdmin):
    list_display = ('duns_number', 'status', 'created_on')


@admin.register(InvestigationRequest)
class InvestigationRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'created_on')
