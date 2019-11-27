import factory

from company.constants import LegalStatusChoices, MonitoringStatusChoices, RegistrationNumberChoices
from company.models import Country


class CompanyFactory(factory.django.DjangoModelFactory):

    primary_name = factory.Sequence(lambda n: f'Company {n+1}')
    duns_number = factory.Sequence(lambda n: str(n).zfill(9))
    year_started = 2000
    address_country = factory.LazyAttribute(lambda _: Country.objects.first())
    monitoring_status = MonitoringStatusChoices.not_enabled.name
    legal_status = LegalStatusChoices.corporation.name

    is_out_of_business = False

    class Meta:
        model = 'company.Company'


class RegistrationNumberFactory(factory.django.DjangoModelFactory):

    registration_number = factory.Sequence(lambda n: str(n).zfill(9))
    registration_type = RegistrationNumberChoices.uk_vat_number

    class Meta:
        model = 'company.RegistrationNumber'


class IndustryCodeFactory(factory.django.DjangoModelFactory):

    code = factory.Sequence(lambda n: str(n).zfill(9))

    class Meta:
        model = 'company.IndustryCode'


class PrimaryIndustryCodeFactory(factory.django.DjangoModelFactory):

    usSicV4 = factory.Sequence(lambda n: str(n).zfill(4))

    class Meta:
        model = 'company.PrimaryIndustryCode'
