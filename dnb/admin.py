from django.contrib import admin

from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('duns_number', 'business_name', 'is_out_of_business', 'created', 'last_updated')
    list_filter = ('is_out_of_business', 'is_employees_number_estimated', 'is_annual_sales_estimated')
    search_fields = ('duns_number', 'business_name')
