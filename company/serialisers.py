from rest_framework import serializers

from company.models import Company, IndustryCode, PrimaryIndustryCode, RegistrationNumber


class RegistrationNumberSerialiser(serializers.ModelSerializer):

    class Meta:
        model = RegistrationNumber
        read_only = True
        exclude = ['id', 'company']


class IndustryCodeSerialiser(serializers.ModelSerializer):

    class Meta:
        model = IndustryCode
        read_only = True
        exclude = ['id', 'company']


class PrimaryIndustryCodeSerialiser(serializers.ModelSerializer):

    class Meta:
        model = PrimaryIndustryCode
        read_only = True
        exclude = ['id', 'company']


class CompanySerialiser(serializers.ModelSerializer):
    address_country = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field='iso_alpha2'
    )

    registered_address_country = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field='iso_alpha2'
    )

    registration_numbers = RegistrationNumberSerialiser(many=True)
    industry_codes = IndustryCodeSerialiser(many=True)
    primary_industry_codes = PrimaryIndustryCodeSerialiser(many=True)

    class Meta:
        model = Company
        fields = [
            'last_updated',
            'duns_number',
            'global_ultimate_duns_number',
            'primary_name',
            'global_ultimate_primary_name',
            'trading_names',
            'domain',
            'address_line_1',
            'address_line_2',
            'address_town',
            'address_county',
            'address_country',
            'address_postcode',
            'registered_address_line_1',
            'registered_address_line_2',
            'registered_address_town',
            'registered_address_county',
            'registered_address_country',
            'registered_address_postcode',
            'line_of_business',
            'is_out_of_business',
            'year_started',
            'global_ultimate_duns_number',
            'employee_number',
            'is_employees_number_estimated',
            'annual_sales',
            'annual_sales_currency',
            'is_annual_sales_estimated',
            'legal_status',
            'registration_numbers',
            'primary_industry_codes',
            'industry_codes',
        ]