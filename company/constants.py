from core.types import StrEnum


class LegalStatusChoices(StrEnum):
    unknown = 'Unknown'
    unspecified = 'Unspecified'
    corporation = 'Corporation'
    joint_venture = 'Joint Venture'
    partnership = 'Partnership'
    proprietorship = 'Proprietorship'
    government_body = 'Government Body'
    cooperative = 'Cooperative'
    non_profit_organisation = 'Non Profit Organization'
    local_government_body = 'Local Government Body'
    foreign_company = 'Foreign Company'


class RegistrationNumberChoices(StrEnum):
    uk_companies_house_number = 'UK Companies house number'
    uk_vat_number = 'VAT Registration number'


class MonitoringStatusChoices(StrEnum):
    not_enabled = 'Not enabled'
    pending = 'Pending submission'
    enabled = 'Enabled'
    failed = 'Failed'


class ChangeRequestStatus(StrEnum):
    pending = 'Pending submission'
    submitted = 'Submitted'


ADDRESS_FIELDS = ['line_1', 'line_2', 'town', 'county', 'country', 'postcode']
