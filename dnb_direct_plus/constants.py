from company.constants import LegalStatusChoices, RegistrationNumberChoices


# Map the BusinessEntityType field to our local status field
LEGAL_STATUS_MAPPING = {
    0: LegalStatusChoices.unknown,
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

OPERATING_STATUS_ACTIVE = 9074  # indicates that a company is active

RELIABILITY_CODE_ACTUAL = 9092

INFORMATION_SCOPE_CONSOLIDATED = 9067

SEARCH_QUERY_TO_DNB_FIELD_MAPPING = {
    'duns_number': 'duns',
    'search_term': 'searchTerm',
    'is_out_of_business': 'isOutOfBusiness',
    'address_country': 'countryISOAlpha2Code',
    'telephone_number': 'telephoneNumber',
    'domain': 'domain',
    'registration_numbers': 'registrationNumbers',
    'address_town': 'addressLocality',
    'address_line_1': 'streetAddressLine1',
    'address_region': 'addressRegion',
    'primary_name': 'primaryName',
    'postal_code': 'postalCode',
    'trading_names': 'tradeStyleName',
    'page_size': 'pageSize',
    'page_number': 'pageNumber',
}

SEARCH_QUERY_TO_DNB_FIELD_MAPPING_V2 = {
    'duns_number': 'duns',
    'search_term': 'name',
    'address_country': 'countryISOAlpha2Code',
    'telephone_number': 'telephoneNumber',
    'domain': 'url',
    'address_town': 'addressLocality',
    'address_line_1': 'streetAddressLine1',
    'address_region': 'addressRegion',
    'postal_code': 'postalCode',
}

DEPRECATED_SEARCH_QUERY_PARAMS_V2 = [
    'is_out_of_business',
    'registration_numbers',
    'primary_name',
    'trading_names',
    'page_size',
    'page_number',
]

ABBREVIATED_AREA_MAPPING = {
    'US': {
        'AL': 'Alabama',
        'AK': 'Alaska',
        'AZ': 'Arizona',
        'AR': 'Arkansas',
        'CA': 'California',
        'CO': 'Colorado',
        'CT': 'Connecticut',
        'DE': 'Delaware',
        'FL': 'Florida',
        'GA': 'Georgia',
        'HI': 'Hawaii',
        'ID': 'Idaho',
        'IL': 'Illinois',
        'IN': 'Indiana',
        'IA': 'Iowa',
        'KS': 'Kansas',
        'KY': 'Kentucky',
        'LA': 'Louisiana',
        'ME': 'Maine',
        'MD': 'Maryland',
        'MA': 'Massachusetts',
        'MI': 'Michigan',
        'MN': 'Minnesota',
        'MS': 'Mississippi',
        'MO': 'Missouri',
        'MT': 'Montana',
        'NE': 'Nebraska',
        'NV': 'Nevada',
        'NH': 'New Hampshire',
        'NJ': 'New Jersey',
        'NM': 'New Mexico',
        'NY': 'New York',
        'NC': 'North Carolina',
        'ND': 'North Dakota',
        'OH': 'Ohio',
        'OK': 'Oklahoma',
        'OR': 'Oregon',
        'PA': 'Pennsylvania',
        'RI': 'Rhode Island',
        'SC': 'South Carolina',
        'SD': 'South Dakota',
        'TN': 'Tennessee',
        'TX': 'Texas',
        'UT': 'Utah',
        'VT': 'Vermont',
        'VA': 'Virginia',
        'WA': 'Washington',
        'WV': 'West Virginia',
        'WI': 'Wisconsin',
        'WY': 'Wyoming',
        'DC': 'District of Columbia',
        'AS': 'American Samoa',
        'GU': 'Guam',
        'MP': 'Northern Mariana Islands',
        'PR': 'Puerto Rico',
        'UM': 'United States Minor Outlying Islands',
        'VI': 'U.S. Virgin Islands',
    },
    'CA': {
        'AB': 'Alberta',
        'BC': 'British Columbia',
        'MB': 'Manitoba',
        'NB': 'New Brunswick',
        'NL': 'Newfoundland and Labrador',
        'NS': 'Nova Scotia',
        'ON': 'Ontario',
        'PE': 'Prince Edward Island',
        'QC': 'Quebec',
        'SK': 'Saskatchewan',
        'NT': 'Northwest Territories',
        'NU': 'Nunavut',
        'YT': 'Yukon'
    }
}
