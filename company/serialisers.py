from django.utils.functional import cached_property

from rest_framework import serializers

from company.constants import ADDRESS_FIELDS
from company.models import (
    ChangeRequest,
    Company,
    Country,
    IndustryCode,
    InvestigationRequest,
    PrimaryIndustryCode,
    RegistrationNumber,
)


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
            'address_area_name',
            'address_area_abbrev_name',
            'address_country',
            'address_postcode',
            'registered_address_line_1',
            'registered_address_line_2',
            'registered_address_town',
            'registered_address_county',
            'registered_address_area_name',
            'registered_address_area_abbrev_name',
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


class ChangeRequestChangesSerialiser(CompanySerialiser):
    """
    Serialised representation of company field changes that can be requested.
    """
    address_country = serializers.CharField(max_length=2, required=False)
    registered_address_country = serializers.CharField(max_length=2, required=False)

    class Meta:
        model = Company
        fields = [
            'primary_name',
            'trading_names',
            'domain',
            'address_line_1',
            'address_line_2',
            'address_town',
            'address_county',
            'address_area_name',
            'address_area_abbrev_name',
            'address_country',
            'address_postcode',
            'registered_address_line_1',
            'registered_address_line_2',
            'registered_address_town',
            'registered_address_county',
            'registered_address_area_name',
            'registered_address_area_abbrev_name',
            'registered_address_country',
            'registered_address_postcode',
            'employee_number',
            'annual_sales',
            'annual_sales_currency',
        ]
        extra_kwargs = {
            'primary_name': {
                'required': False,
            },
            'annual_sales': {
                'required': False,
                'allow_null': False,
            },
            'employee_number': {
                'required': False,
                'allow_null': False,
            },
        }

    @cached_property
    def _country_slugs(self):
        return Country.objects.all().values_list('iso_alpha2', flat=True)

    def _validate_country_slug(self, value):
        if value not in self._country_slugs:
            raise serializers.ValidationError('This is not a valid ISO Alpha2 country code.')

    def _ensure_address_all_or_nothing(self, fields_prefix, data):
        address_fields = {f'{fields_prefix}_{field}' for field in ADDRESS_FIELDS}
        address_fields_in_data = address_fields.intersection(data.keys())
        if address_fields_in_data and address_fields_in_data != address_fields:
            message = f"If any '{fields_prefix}' fields are set, all '{fields_prefix}' fields must be set."
            raise serializers.ValidationError(message)

    def validate_address_country(self, value):
        """
        Validate that the address_country field is a valid ISO alpha2 slug.
        """
        self._validate_country_slug(value)
        return value

    def validate_registered_address_country(self, value):
        """
        Validate that the registered_address_country field is a valid ISO alpha2 slug.
        """
        self._validate_country_slug(value)
        return value

    def validate(self, data):
        """
        Ensure that address and registered_address fields are all or nothing i.e.
        if one address field is set, raise a 400 error if all of the rest are not set.
        """
        self._ensure_address_all_or_nothing('address', data)
        self._ensure_address_all_or_nothing('registered_address', data)
        return data


class ChangeRequestSerialiser(serializers.ModelSerializer):
    """
    Serialised representation of a ChangeRequest.
    """
    changes = ChangeRequestChangesSerialiser()

    class Meta:
        model = ChangeRequest
        fields = [
            'id',
            'duns_number',
            'changes',
            'status',
            'created_on',
        ]

    def create(self, validated_data):
        """
        Create the ChangeRequest record.
        """
        change_request = ChangeRequest(**validated_data)
        change_request.save()
        return change_request


class CompanyDetailsSerialiser(CompanySerialiser):
    """
    Serialised representation of `company_details` JSON field
    in the InvestigationRequest model.
    """

    telephone_number = serializers.CharField(max_length=20, required=False)
    address_country = serializers.CharField(max_length=2, required=True)

    @cached_property
    def _country_slugs(self):
        return Country.objects.all().values_list('iso_alpha2', flat=True)

    def _validate_country_slug(self, value):
        if value not in self._country_slugs:
            raise serializers.ValidationError('This is not a valid ISO Alpha2 country code.')

    def validate_address_country(self, value):
        """
        Validate that the address_country field is a valid ISO alpha2 slug.
        """
        self._validate_country_slug(value)
        return value

    def validate(self, data):
        """
        Cross-field validation e.g. ensuring that either domain or
        telephone_number is present.
        """
        super().validate(data)
        if 'domain' not in data and 'telephone_number' not in data:
            raise serializers.ValidationError(
                'Either domain or telephone_number must be provided for D&B investigation.'
            )
        return data

    class Meta:
        model = Company
        fields = (
            'primary_name',
            'domain',
            'telephone_number',
            'address_line_1',
            'address_line_2',
            'address_town',
            'address_county',
            'address_area_name',
            'address_area_abbrev_name',
            'address_country',
            'address_postcode',
        )
        extra_kwargs = {
            'address_line_1': {
                'required': True,
            },
            'address_town': {
                'required': True,
            },
        }

class InvestigationRequestSerializer(serializers.ModelSerializer):
    """
    Serialised representation of the Investigation object.
    """
    company_details = CompanyDetailsSerialiser()

    class Meta:
        model = InvestigationRequest
        fields = (
            'id',
            'company_details',
            'status',
            'created_on',
            'submitted_on',
        )

    def create(self, validated_data):
        """
        Create the ChangeRequest record.
        """
        investigation_request = InvestigationRequest(**validated_data)
        investigation_request.save()
        return investigation_request
        