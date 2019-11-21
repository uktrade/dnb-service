from django.contrib import admin

from .models import Company, Country, IndustryCode, PrimaryIndustryCode, RegistrationNumber


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
