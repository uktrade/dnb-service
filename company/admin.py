from django.contrib import admin

from .models import Company, Country


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('duns_number', 'trading_name_list', 'is_out_of_business', 'created', 'last_updated')
    list_filter = ('is_out_of_business', 'is_employees_number_estimated', 'is_annual_sales_estimated')
    search_fields = ('duns_number', 'business_name')

    def trading_name_list(self, obj):
        return ', '.split(obj.trading_names)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'iso_alpha2', 'iso_alpha3', 'iso_numeric')
