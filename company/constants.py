from core.types import StrEnum


class LastUpdatedSource(StrEnum):
    worldbase = 'Worldbase file'
    api = 'API'


class LegalStatusChoices(StrEnum):
    unknown = 'Unknown'
    unspecified = 'Unspecified'
    corporation = 'Corporation'
    joint_venture = 'Joint Venture'
    partnership = 'Partnership'
    proprietorship = 'Proprietorship'
    government_body = 'Government Body'
    cooperative = 'Cooperative'
    non_profit_organisation = 'Non Profit Organisation'
    local_government_body = 'Local Government Body'
    foreign_company = 'Foreign Company'


class RegistrationNumberChoices(StrEnum):
    uk_companies_house_number = 'UK Companies house number'
    uk_vat_number = 'VAT Registration number'
