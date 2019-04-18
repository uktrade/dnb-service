from core.types import StrEnum


class LastUpdatedSource(StrEnum):
    worldbase = 'Worldbase file'
    api = 'API'


class LegalStatusChoices(StrEnum):
    corporation = 'Corporation'
    joint_venture = 'Joint venture'
    partnership_of_unknown_type = 'Partnership Of Unknown Type'
    proprietorship = 'Proprietorship'
    government_body = 'Government Body'
    cooperative = 'Cooperative'
    non_profit_organisation = 'Non Profit Organization'
    local_governmenet_body = 'Local Government Body'
    foreign_company = 'Foreign Company'
    master_limited_partnership = 'Master Limited Partnership'
    limited_liability = 'Limited Liability'
    private_limited_company = 'Private Limited Company'


class RegistrationNumberChoices(StrEnum):
    uk_companies_house_number = 'UK Companies house number'
    uk_vat_number = 'VAT Registration number'
