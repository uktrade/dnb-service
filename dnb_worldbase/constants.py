from enum import Enum

from company.constants import LegalStatusChoices, RegistrationNumberChoices

DNB_COUNTRY_CODE_MAPPING = {
    '897': None,  # ABU DHABI
    '901': None,  # ADMIRALTY ISLANDS
    '005': 'AF',  # AFGHANISTAN
    '898': None,  # AJMAN
    '009': 'AL',  # ALBANIA
    '013': 'DZ',  # ALGERIA
    '021': 'AD',  # ANDORRA
    '025': 'AO',  # ANGOLA
    '027': 'AI',  # ANGUILLA
    '028': 'AG',  # ANTIGUA & BARBUDA
    '033': 'AR',  # ARGENTINA
    '900': 'AM',  # ARMENIA
    '034': 'AW',  # ARUBA
    '035': 'AC',  # ASCENSION ISLAND
    '037': 'AU',  # AUSTRALIA
    '041': 'AT',  # AUSTRIA
    '905': 'AZ',  # AZERBAIJAN
    '049': 'BS',  # BAHAMAS
    '053': 'BH',  # BAHRAIN
    '061': 'BD',  # BANGLADESH
    '065': 'BB',  # BARBADOS
    '915': 'BY',  # BELARUS
    '069': 'BE',  # BELGIUM
    '071': 'BZ',  # BELIZE
    '072': 'BJ',  # BENIN
    '073': 'BM',  # BERMUDA
    '077': 'BT',  # BHUTAN
    '081': 'BO',  # BOLIVIA
    '083': 'BQ',  # BONAIRE ST EUST SABA
    '910': 'BA',  # BOSNIA-HERZEGOVINA
    '085': 'BW',  # BOTSWANA
    '089': 'BR',  # BRAZIL
    '091': 'IO',  # BRITISH INDIAN OCEAN
    '096': 'BN',  # BRUNEI
    '100': 'BG',  # BULGARIA
    '101': 'BF',  # BURKINA FASO
    '113': 'BI',  # BURUNDI
    '379': 'KH',  # CAMBODIA
    '117': 'CM',  # CAMEROON
    '121': 'CA',  # CANADA
    '127': 'CV',  # CAPE VERDE
    '135': None,  # CAROLINE ISLANDS
    '131': 'KY',  # CAYMAN ISLANDS
    '141': 'CF',  # CENTRAL AFRICAN REP
    '149': 'TD',  # CHAD
    '153': 'CL',  # CHILE
    '157': 'CN',  # CHINA
    '916': None,  # CHRISTMAS ISLAND
    '165': 'CO',  # COLOMBIA
    '169': 'KM',  # COMOROS
    '173': 'CG',  # CONGO
    '865': 'CD',  # CONGO DEMOCRATIC REP
    '175': 'CK',  # COOK ISLANDS
    '177': 'CR',  # COSTA RICA
    '179': 'HR',  # CROATIA
    '181': 'CU',  # CUBA
    '183': 'CW',  # CURACAO
    '185': 'CY',  # CYPRUS
    '190': 'CZ',  # CZECH REPUBLIC
    '197': 'DK',  # DENMARK
    '198': 'DJ',  # DJIBOUTI
    '199': 'DM',  # DOMINICA
    '201': 'DO',  # DOMINICAN REPUBLIC
    '917': None,  # DUBAI
    '205': 'TL',  # EAST TIMOR
    '209': 'EC',  # ECUADOR
    '029': 'EG',  # EGYPT
    '213': 'SV',  # EL SALVADOR
    '785': 'GB',  # ENGLAND
    '217': 'GQ',  # EQUATORIAL GUINEA
    '919': 'ER',  # ERITREA
    '219': 'EE',  # ESTONIA
    '221': 'ET',  # ETHIOPIA
    '229': 'FK',  # FALKLAND ISLANDS
    '225': 'FO',  # FAROE ISLANDS
    '233': 'FJ',  # FIJI
    '237': 'FI',  # FINLAND
    '241': 'FR',  # FRANCE
    '245': 'GF',  # FRENCH GUIANA
    '249': 'PF',  # FRENCH POLYNESIA
    '918': None,  # FUJAIRAH
    '253': 'GA',  # GABON
    '261': 'GM',  # GAMBIA
    '920': 'GE',  # GEORGIA
    '269': 'DE',  # GERMANY
    '273': 'GH',  # GHANA
    '277': 'GI',  # GIBRALTAR
    '285': 'GR',  # GREECE
    '289': 'GL',  # GREENLAND
    '291': 'GD',  # GRENADA
    '293': 'GP',  # GUADELOUPE
    '297': 'GU',  # GUAM
    '301': 'GT',  # GUATEMALA
    '302': 'GG',  # GUERNSEY
    '305': 'GN',  # GUINEA
    '303': 'GW',  # GUINEA-BISSAU
    '309': 'GY',  # GUYANA
    '313': 'HT',  # HAITI
    '317': 'HN',  # HONDURAS
    '321': 'HK',  # HONG KONG
    '325': 'HU',  # HUNGARY
    '329': 'IS',  # ICELAND
    '333': 'IN',  # INDIA
    '337': 'ID',  # INDONESIA
    '341': 'IR',  # IRAN
    '345': 'IQ',  # IRAQ
    '349': 'IE',  # IRELAND
    '351': 'IM',  # ISLE OF MAN
    '353': 'IL',  # ISRAEL
    '357': 'IT',  # ITALY
    '361': 'CI',  # IVORY COAST
    '365': 'JM',  # JAMAICA
    '369': 'JP',  # JAPAN
    '374': 'JE',  # JERSEY
    '377': 'JO',  # JORDAN
    '925': 'KZ',  # KAZAKHSTAN
    '381': 'KE',  # KENYA
    '387': 'KI',  # KIRIBATI
    '389': 'KP',  # KOREA NORTH
    '393': 'KR',  # KOREA REP OF
    '392': 'XK',  # KOSOVO
    '397': 'KW',  # KUWAIT
    '930': 'KG',  # KYRGYZSTAN
    '401': 'LA',  # LAOS
    '935': 'LV',  # LATVIA
    '405': 'LB',  # LEBANON
    '409': 'LS',  # LESOTHO
    '413': 'LR',  # LIBERIA
    '417': 'LY',  # LIBYA
    '421': 'LI',  # LIECHTENSTEIN
    '425': 'LT',  # LITHUANIA
    '429': 'LU',  # LUXEMBOURG
    '433': 'MO',  # MACAO
    '965': 'MK',  # MACEDONIA
    '441': 'MG',  # MADAGASCAR
    '445': 'MW',  # MALAWI
    '449': 'MY',  # MALAYSIA
    '453': 'MV',  # MALDIVES
    '457': 'ML',  # MALI
    '461': 'MT',  # MALTA
    '469': 'MH',  # MARSHALL ISLANDS
    '473': 'MQ',  # MARTINIQUE
    '477': 'MR',  # MAURITANIA
    '481': 'MU',  # MAURITIUS
    '937': 'YT',  # MAYOTTE
    '489': 'MX',  # MEXICO
    '491': 'FM',  # MICRONESIA FED ST
    '938': 'MI',  # MIDWAY ISLAND
    '940': 'MD',  # MOLDOVA
    '497': 'MC',  # MONACO
    '499': 'MN',  # MONGOLIA
    '498': 'ME',  # MONTENEGRO
    '501': 'MS',  # MONTSERRAT
    '505': 'MA',  # MOROCCO
    '509': 'MZ',  # MOZAMBIQUE
    '510': 'MM',  # MYANMAR
    '511': 'NA',  # NAMIBIA
    '513': 'NR',  # NAURU
    '517': 'NP',  # NEPAL
    '521': 'NL',  # NETHERLANDS
    '525': 'AN',  # NETHERLANDS ANTILLES
    '529': 'NC',  # NEW CALEDONIA
    '537': 'NZ',  # NEW ZEALAND
    '541': 'NI',  # NICARAGUA
    '545': 'NE',  # NIGER
    '549': 'NG',  # NIGERIA
    '570': 'NU',  # NIUE
    '552': 'NF',  # NORFOLK ISLAND
    '793': 'GB',  # NORTHERN IRELAND
    '551': 'MP',  # NORTHERN MARIANA IS
    '553': 'NO',  # NORWAY
    '561': 'OM',  # OMAN
    '565': 'PK',  # PAKISTAN
    '567': 'PW',  # PALAU
    '568': 'PS',  # PALESTINIAN TERR
    '569': 'PA',  # PANAMA
    '573': 'PG',  # PAPUA NEW GUINEA
    '581': 'PY',  # PARAGUAY
    '585': 'PE',  # PERU
    '589': 'PH',  # PHILIPPINES
    '593': 'PN',  # PITCAIRN ISLAND
    '597': 'PL',  # POLAND
    '601': 'PT',  # PORTUGAL
    '613': 'QA',  # QATAR
    '942': None,  # RAS AL-KHAIMAH
    '617': 'RE',  # REUNION
    '620': 'RO',  # ROMANIA
    '622': 'RU',  # RUSSIAN FEDERATION
    '623': 'RW',  # RWANDA
    '641': 'WS',  # SAMOA
    '017': 'AS',  # SAMOA AMERICAN
    '649': 'SM',  # SAN MARINO
    '653': 'ST',  # SAO TOME & PRINCIPE
    '657': 'SA',  # SAUDI ARABIA
    '797': 'GB',  # SCOTLAND
    '661': 'SN',  # SENEGAL
    '663': 'RS',  # SERBIA
    '861': 'YU',  # YUGOSLAVIA
    '665': 'SC',  # SEYCHELLES
    '943': None,  # SHARJAH
    '669': 'SL',  # SIERRA LEONE
    '677': 'SG',  # SINGAPORE
    '680': 'SK',  # SLOVAKIA
    '678': 'SI',  # SLOVENIA
    '679': 'SB',  # SOLOMON ISLANDS
    '681': 'SO',  # SOMALIA
    '685': 'ZA',  # SOUTH AFRICA
    '944': 'GS',  # SOUTH GEORGIA
    '947': 'GS',  # SOUTH SANDWICH IS
    '690': 'SS',  # SOUTH SUDAN
    '693': 'ES',  # SPAIN
    '701': 'LK',  # SRI LANKA
    '625': 'BL',  # ST BARTHELEMY
    '626': 'SH',  # ST HELENA
    '629': 'KN',  # ST KITTS-NEVIS
    '633': 'LC',  # ST LUCIA
    '634': 'SX',  # ST MAARTEN
    '644': 'MF',  # ST MARTIN
    '635': 'PM',  # ST PIERRE MIQUELON
    '637': 'VC',  # ST VINCENT
    '705': 'SD',  # SUDAN
    '709': 'SR',  # SURINAME
    '713': 'SZ',  # SWAZILAND
    '717': 'SE',  # SWEDEN
    '721': 'CH',  # SWITZERLAND
    '725': 'SY',  # SYRIA
    '161': 'TW',  # TAIWAN
    '945': 'TJ',  # TAJIKISTAN
    '729': 'TZ',  # TANZANIA
    '733': 'TH',  # THAILAND
    '741': 'TG',  # TOGO
    '946': None,  # TOKELAU
    '745': 'TO',  # TONGA
    '749': 'TT',  # TRINIDAD & TOBAGO
    '757': 'TN',  # TUNISIA
    '761': 'TR',  # TURKEY
    '763': None,  # TURKISH REP N CYPRUS
    '950': 'TM',  # TURKMENISTAN
    '765': 'TC',  # TURKS & CAICOS IS
    '767': 'TV',  # TUVALU
    '769': 'UG',  # UGANDA
    '771': 'UA',  # UKRAINE
    '952': None,  # UMM AL-QUWAIN
    '777': 'AE',  # UNITED ARAB EMIRATES
    '790': 'GB',  # UNITED KINGDOM
    '813': 'UY',  # URUGUAY
    '814': 'UM',  # US MINOR OUTLYING IS
    '805': 'US',  # USA
    '955': 'UZ',  # UZBEKISTAN
    '816': 'VU',  # VANUATU
    '819': 'VA',  # VATICAN CITY
    '821': 'VE',  # VENEZUELA
    '829': 'VN',  # VIETNAM
    '093': 'VG',  # VIRGIN ISLANDS UK
    '970': 'UM',  # WAKE ISLAND
    '801': 'GB',  # WALES
    '841': 'WF',  # WALLIS & FUTUNA IS
    '853': 'YE',  # YEMEN
    '857': 'YD',  # YEMEN SOUTH
    '869': 'ZM',  # ZAMBIA
    '873': 'ZW',  # ZIMBABWE
    '000': None,  # Unknown
}

WB_HEADER_FIELDS = [
    '_DUNS_Number', 'DNB_REF_ID', 'DUNS', 'DUNS Recertification Code', 'Filler 1', 'DUNS Number',
    'Business Name', 'Secondary Name', 'Registered Address Indicator', 'Street Address',
    'Street Address 2', 'City Name', 'State/Province Name', 'Country Name', 'City Code',
    'County Code', 'State/Province Code', 'State/Province Abbreviation', 'Country Code',
    'Postal Code for Street Address', 'Continent Code', 'Mailing Address', 'Mailing City Name',
    'Mailing County Name', 'Mailing State/Province Name', 'Mailing Country Name',
    'Mailing City Code', 'Mailing County Code', 'Mailing State/Province Code',
    'Mailing State/Province Abbreviation', 'Mailing Country Code',
    'Postal Code For Mailing Address', 'Mailing Continent Code',
    'National Identification Number', 'National Identification System Code',
    'Country Telephone Access Code', 'Telephone Number', 'Cable Telex', 'Fax Number',
    'Chief Executive Officer Name', 'Chief Executive Officer Title', 'Line of Business',
    'US 1987 SIC 1', 'US 1987 SIC 2', 'US 1987 SIC 3', 'US 1987 SIC 4', 'US 1987 SIC 5',
    'US 1987 SIC 6', 'Primary Local Activity Code', 'Activity Indicator', 'Year Started',
    'Annual Sales Local', 'Annual Sales Indicator', 'Annual Sales in US dollars',
    'Currency Code', 'Employees Here', 'Employees Here Indicator', 'Employees Total',
    'Employees Total Indicator', 'Include Principles Indicator',
    'Import/Export/ Agent Indicator', 'Legal Status', 'Control Indicator', 'Status Code',
    'Subsidiary Code', 'Filler 2', 'Previous DUNS Number', 'Report Date', 'Filler 3',
    'Headquarter/Parent DUNS Number', 'Headquarter/Parent Business Name',
    'Headquarter/Parent Street Address', 'Headquarter/Parents City',
    'Headquarter/Parent State/Province', 'Headquarter/Parent Country Name',
    'Headquarter/Parents City Code', 'Headquarter/Parent County Code',
    'Headquarter/Parent State/Province Abbreviation', 'Headquarter/Parent Country Code',
    'Headquarter/Parent Postal Code', 'Headquarter/Parent Continent Code', 'Filler 4',
    'Domestic Ultimate DUNS Number', 'Domestic Ultimate Business Name',
    'Domestic Ultimate Street Address', 'Domestic Ultimate City Name',
    'Domestic Ultimate State/Province Name', 'Domestic Ultimate City Code',
    'Domestic Ultimate Country Code', 'Domestic Ultimate State Abbreviation',
    'Domestic Ultimate Postal Code', 'Global Ultimate Indicator', 'Filler 5',
    'Global Ultimate DUNS Number', 'Global Ultimate Name', 'Global Ultimate Street Address',
    'Global Ultimate City Name', 'Global Ultimate State/Province',
    'Global Ultimate Country Name', 'Global Ultimate City Code', 'Global Ultimate County Code',
    'Ultimate State/Province Abbreviation', 'Global Ultimate Country Code',
    'Global Ultimate Postal Code', 'Global Ultimate Continent Code', 'Number of Family Members',
    'DIAS Code', 'Hierarchy Code', 'Family Update Date', 'Out of Business indicator',
    'Marketable indicator', 'Delist indicator']

# Worldbase legal status code mapping.
LEGAL_STATUS_CODE_MAPPING = {
    0: LegalStatusChoices.unspecified,
    3: LegalStatusChoices.corporation,
    8: LegalStatusChoices.joint_venture,
    12: LegalStatusChoices.partnership,
    13: LegalStatusChoices.proprietorship,
    50: LegalStatusChoices.government_body,
    100: LegalStatusChoices.cooperative,
    101: LegalStatusChoices.non_profit_organisation,
    118: LegalStatusChoices.local_government_body,
    120: LegalStatusChoices.foreign_company,
}

# Worldbase national ID code mapping. As we are currently only ingesting UK data,
# we only see the Companies House number.
NATIONAL_ID_CODE_MAPPING = {
    12: RegistrationNumberChoices.uk_companies_house_number,
}

BUSINESS_INDICATOR_MAPPING = {
    'Y': True,
    'N': False,
}


class EmployeesIndicator(Enum):
    """
    Indicates if the field Employees Total/Here is an actual value,
    estimated value or not available.
    """

    NOT_AVAILABLE = ''
    ACTUAL = '0'
    LOW_END_OF_RANGE = '1'
    ESTIMATED = '2'
    MODELLED = '3'


class TurnoverIndicator(Enum):
    """
    Indicates if the field 'Annual Sales in US dollars' is an actual value,
    estimated value or not available.
    """

    NOT_AVAILABLE = ''
    ACTUAL = '0'
    LOW_END_OF_RANGE = '1'
    ESTIMATED = '2'
    MODELLED = '3'


class OutOfBusinessIndicator(Enum):
    """Indicates if a business is out of business."""

    OUT_OF_BUSINESS = 'Y'
    NOT_OUT_OF_BUSINESS = 'N'
