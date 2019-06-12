from company.constants import LegalStatusChoices, RegistrationNumberChoices


# Map the BusinessEntityType field to our local status field
LEGAL_STATUS_MAPPING = {
     451: LegalStatusChoices.corporation,  # Corporation
     452: LegalStatusChoices.partnership,  # Partnership
     453: LegalStatusChoices.proprietorship,  # Proprietorship
     454: LegalStatusChoices.government_body,  # National Government Entity
     455: LegalStatusChoices.local_government_body,  # Regional/Local Government Entity
     456: LegalStatusChoices.joint_venture,  # Joint Venture
     457: LegalStatusChoices.non_profit_organisation,  # Non Profit Organisation
     461: LegalStatusChoices.cooperative,  # Co-operative / Mutual Organisation
     469: LegalStatusChoices.foreign_company,  # Foreign Company
     470: LegalStatusChoices.unspecified,  # Miscellaneous / Not Elsewhere Classified
}


REGISTRATION_NUMBER_TYPE_MAPPING = {
     2541: RegistrationNumberChoices.uk_companies_house_number,  # COMPANIES REGISTRY OFFICE Number (GB)
     2550: RegistrationNumberChoices.uk_vat_number,  # Value Added Tax Number (GB)
}


OPERATING_STATUS_ACTIVE = 9074     # indicates that a company is active
