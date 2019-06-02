from rest_framework import serializers

from .models import Company, Country, RegistrationNumber


class RegistrationNumberSerialiser(serializers.ModelSerializer):
    class Meta:
        model = RegistrationNumber
        exclude = ('id',)


class CountrySerialiser(serializers.ModelSerializer):
    class Meta:
        model = Country
        exclude = ('id',)


class CompanySerialiser(serializers.ModelSerializer):
    registration_numbers = RegistrationNumberSerialiser(many=True, read_only=True)
    address_country = CountrySerialiser(read_only=True)
    registered_address_country = CountrySerialiser(read_only=True)

    class Meta:
        model = Company
        exclude = ('id',)
