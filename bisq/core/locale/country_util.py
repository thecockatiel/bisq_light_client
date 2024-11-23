# TODO: complete ?
from typing import Dict, List, Optional
from bisq.core.locale.country import Country
from bisq.core.locale.locale_util import ALL_LOCALES
from bisq.core.locale.region import Region

_region_by_country_code_map = {
    "AF": "AS",  # Afghanistan / region=Asia / subregion=Southern Asia
    "AX": "EU",  # Åland Islands / region=Europe / subregion=Northern Europe
    "AL": "EU",  # Albania / region=Europe / subregion=Southern Europe
    "DZ": "AF",  # Algeria / region=Africa / subregion=Northern Africa
    "AS": "OC",  # American Samoa / region=Oceania / subregion=Polynesia
    "AD": "EU",  # Andorra / region=Europe / subregion=Southern Europe
    "AO": "AF",  # Angola / region=Africa / subregion=Middle Africa
    "AI": "AM",  # Anguilla / region=Americas / subregion=Caribbean
    "AG": "AM",  # Antigua and Barbuda / region=Americas / subregion=Caribbean
    "AR": "AM",  # Argentina / region=Americas / subregion=South America
    "AM": "AS",  # Armenia / region=Asia / subregion=Western Asia
    "AW": "AM",  # Aruba / region=Americas / subregion=Caribbean
    "AU": "OC",  # Australia / region=Oceania / subregion=Australia and New Zealand
    "AT": "EU",  # Austria / region=Europe / subregion=Western Europe
    "AZ": "AS",  # Azerbaijan / region=Asia / subregion=Western Asia
    "BS": "AM",  # Bahamas / region=Americas / subregion=Caribbean
    "BH": "AS",  # Bahrain / region=Asia / subregion=Western Asia
    "BD": "AS",  # Bangladesh / region=Asia / subregion=Southern Asia
    "BB": "AM",  # Barbados / region=Americas / subregion=Caribbean
    "BY": "EU",  # Belarus / region=Europe / subregion=Eastern Europe
    "BE": "EU",  # Belgium / region=Europe / subregion=Western Europe
    "BZ": "AM",  # Belize / region=Americas / subregion=Central America
    "BJ": "AF",  # Benin / region=Africa / subregion=Western Africa
    "BM": "AM",  # Bermuda / region=Americas / subregion=Northern America
    "BT": "AS",  # Bhutan / region=Asia / subregion=Southern Asia
    "BO": "AM",  # Bolivia / region=Americas / subregion=South America
    "BQ": "AM",  # Bonaire / region=Americas / subregion=Caribbean
    "BA": "EU",  # Bosnia and Herzegovina / region=Europe / subregion=Southern Europe
    "BW": "AF",  # Botswana / region=Africa / subregion=Southern Africa
    "BR": "AM",  # Brazil / region=Americas / subregion=South America
    "IO": "AF",  # British Indian Ocean Territory / region=Africa / subregion=Eastern Africa
    "UM": "AM",  # United States Minor Outlying Islands / region=Americas / subregion=Northern America
    "VG": "AM",  # Virgin Islands (British) / region=Americas / subregion=Caribbean
    "VI": "AM",  # Virgin Islands (U.S.) / region=Americas / subregion=Caribbean
    "BN": "AS",  # Brunei / region=Asia / subregion=South-Eastern Asia
    "BG": "EU",  # Bulgaria / region=Europe / subregion=Eastern Europe
    "BF": "AF",  # Burkina Faso / region=Africa / subregion=Western Africa
    "BI": "AF",  # Burundi / region=Africa / subregion=Eastern Africa
    "KH": "AS",  # Cambodia / region=Asia / subregion=South-Eastern Asia
    "CM": "AF",  # Cameroon / region=Africa / subregion=Middle Africa
    "CA": "AM",  # Canada / region=Americas / subregion=Northern America
    "CV": "AF",  # Cabo Verde / region=Africa / subregion=Western Africa
    "KY": "AM",  # Cayman Islands / region=Americas / subregion=Caribbean
    "CF": "AF",  # Central African Republic / region=Africa / subregion=Middle Africa
    "TD": "AF",  # Chad / region=Africa / subregion=Middle Africa
    "CL": "AM",  # Chile / region=Americas / subregion=South America
    "CN": "AS",  # China / region=Asia / subregion=Eastern Asia
    "CX": "OC",  # Christmas Island / region=Oceania / subregion=Australia and New Zealand
    "CC": "OC",  # Cocos Islands / region=Oceania / subregion=Australia and New Zealand
    "CO": "AM",  # Colombia / region=Americas / subregion=South America
    "KM": "AF",  # Comoros / region=Africa / subregion=Eastern Africa
    "CG": "AF",  # Congo / region=Africa / subregion=Middle Africa
    "CD": "AF",  # DR Congo / region=Africa / subregion=Middle Africa
    "CK": "OC",  # Cook Islands / region=Oceania / subregion=Polynesia
    "CR": "AM",  # Costa Rica / region=Americas / subregion=Central America
    "HR": "EU",  # Croatia / region=Europe / subregion=Southern Europe
    "CU": "AM",  # Cuba / region=Americas / subregion=Caribbean
    "CW": "AM",  # Curaçao / region=Americas / subregion=Caribbean
    "CY": "EU",  # Cyprus / region=Europe / subregion=Southern Europe
    "CZ": "EU",  # Czech Republic / region=Europe / subregion=Eastern Europe
    "DK": "EU",  # Denmark / region=Europe / subregion=Northern Europe
    "DJ": "AF",  # Djibouti / region=Africa / subregion=Eastern Africa
    "DM": "AM",  # Dominica / region=Americas / subregion=Caribbean
    "DO": "AM",  # Dominican Republic / region=Americas / subregion=Caribbean
    "EC": "AM",  # Ecuador / region=Americas / subregion=South America
    "EG": "AF",  # Egypt / region=Africa / subregion=Northern Africa
    "SV": "AM",  # El Salvador / region=Americas / subregion=Central America
    "GQ": "AF",  # Equatorial Guinea / region=Africa / subregion=Middle Africa
    "ER": "AF",  # Eritrea / region=Africa / subregion=Eastern Africa
    "EE": "EU",  # Estonia / region=Europe / subregion=Northern Europe
    "ET": "AF",  # Ethiopia / region=Africa / subregion=Eastern Africa
    "FK": "AM",  # Falkland Islands / region=Americas / subregion=South America
    "FO": "EU",  # Faroe Islands / region=Europe / subregion=Northern Europe
    "FJ": "OC",  # Fiji / region=Oceania / subregion=Melanesia
    "FI": "EU",  # Finland / region=Europe / subregion=Northern Europe
    "FR": "EU",  # France / region=Europe / subregion=Western Europe
    "GF": "AM",  # French Guiana / region=Americas / subregion=South America
    "PF": "OC",  # French Polynesia / region=Oceania / subregion=Polynesia
    "TF": "AF",  # French Southern Territories / region=Africa / subregion=Southern Africa
    "GA": "AF",  # Gabon / region=Africa / subregion=Middle Africa
    "GM": "AF",  # Gambia / region=Africa / subregion=Western Africa
    "GE": "AS",  # Georgia / region=Asia / subregion=Western Asia
    "DE": "EU",  # Germany / region=Europe / subregion=Western Europe
    "GH": "AF",  # Ghana / region=Africa / subregion=Western Africa
    "GI": "EU",  # Gibraltar / region=Europe / subregion=Southern Europe
    "GR": "EU",  # Greece / region=Europe / subregion=Southern Europe
    "GL": "AM",  # Greenland / region=Americas / subregion=Northern America
    "GD": "AM",  # Grenada / region=Americas / subregion=Caribbean
    "GP": "AM",  # Guadeloupe / region=Americas / subregion=Caribbean
    "GU": "OC",  # Guam / region=Oceania / subregion=Micronesia
    "GT": "AM",  # Guatemala / region=Americas / subregion=Central America
    "GG": "EU",  # Guernsey / region=Europe / subregion=Northern Europe
    "GN": "AF",  # Guinea / region=Africa / subregion=Western Africa
    "GW": "AF",  # Guinea-Bissau / region=Africa / subregion=Western Africa
    "GY": "AM",  # Guyana / region=Americas / subregion=South America
    "HT": "AM",  # Haiti / region=Americas / subregion=Caribbean
    "VA": "EU",  # Holy See / region=Europe / subregion=Southern Europe
    "HN": "AM",  # Honduras / region=Americas / subregion=Central America
    "HK": "AS",  # Hong Kong / region=Asia / subregion=Eastern Asia
    "HU": "EU",  # Hungary / region=Europe / subregion=Eastern Europe
    "IS": "EU",  # Iceland / region=Europe / subregion=Northern Europe
    "IN": "AS",  # India / region=Asia / subregion=Southern Asia
    "ID": "AS",  # Indonesia / region=Asia / subregion=South-Eastern Asia
    "CI": "AF",  # Côte d'Ivoire / region=Africa / subregion=Western Africa
    "IR": "AS",  # Iran / region=Asia / subregion=Southern Asia
    "IQ": "AS",  # Iraq / region=Asia / subregion=Western Asia
    "IE": "EU",  # Ireland / region=Europe / subregion=Northern Europe
    "IM": "EU",  # Isle of Man / region=Europe / subregion=Northern Europe
    "IL": "AS",  # Israel / region=Asia / subregion=Western Asia
    "IT": "EU",  # Italy / region=Europe / subregion=Southern Europe
    "JM": "AM",  # Jamaica / region=Americas / subregion=Caribbean
    "JP": "AS",  # Japan / region=Asia / subregion=Eastern Asia
    "JE": "EU",  # Jersey / region=Europe / subregion=Northern Europe
    "JO": "AS",  # Jordan / region=Asia / subregion=Western Asia
    "KZ": "AS",  # Kazakhstan / region=Asia / subregion=Central Asia
    "KE": "AF",  # Kenya / region=Africa / subregion=Eastern Africa
    "KI": "OC",  # Kiribati / region=Oceania / subregion=Micronesia
    "KW": "AS",  # Kuwait / region=Asia / subregion=Western Asia
    "KG": "AS",  # Kyrgyzstan / region=Asia / subregion=Central Asia
    "LA": "AS",  # Laos / region=Asia / subregion=South-Eastern Asia
    "LV": "EU",  # Latvia / region=Europe / subregion=Northern Europe
    "LB": "AS",  # Lebanon / region=Asia / subregion=Western Asia
    "LS": "AF",  # Lesotho / region=Africa / subregion=Southern Africa
    "LR": "AF",  # Liberia / region=Africa / subregion=Western Africa
    "LY": "AF",  # Libya / region=Africa / subregion=Northern Africa
    "LI": "EU",  # Liechtenstein / region=Europe / subregion=Western Europe
    "LT": "EU",  # Lithuania / region=Europe / subregion=Northern Europe
    "LU": "EU",  # Luxembourg / region=Europe / subregion=Western Europe
    "MO": "AS",  # Macao / region=Asia / subregion=Eastern Asia
    "MK": "EU",  # Macedonia / region=Europe / subregion=Southern Europe
    "MG": "AF",  # Madagascar / region=Africa / subregion=Eastern Africa
    "MW": "AF",  # Malawi / region=Africa / subregion=Eastern Africa
    "MY": "AS",  # Malaysia / region=Asia / subregion=South-Eastern Asia
    "MV": "AS",  # Maldives / region=Asia / subregion=Southern Asia
    "ML": "AF",  # Mali / region=Africa / subregion=Western Africa
    "MT": "EU",  # Malta / region=Europe / subregion=Southern Europe
    "MH": "OC",  # Marshall Islands / region=Oceania / subregion=Micronesia
    "MQ": "AM",  # Martinique / region=Americas / subregion=Caribbean
    "MR": "AF",  # Mauritania / region=Africa / subregion=Western Africa
    "MU": "AF",  # Mauritius / region=Africa / subregion=Eastern Africa
    "YT": "AF",  # Mayotte / region=Africa / subregion=Eastern Africa
    "MX": "AM",  # Mexico / region=Americas / subregion=Central America
    "FM": "OC",  # Micronesia / region=Oceania / subregion=Micronesia
    "MD": "EU",  # Moldova / region=Europe / subregion=Eastern Europe
    "MC": "EU",  # Monaco / region=Europe / subregion=Western Europe
    "MN": "AS",  # Mongolia / region=Asia / subregion=Eastern Asia
    "ME": "EU",  # Montenegro / region=Europe / subregion=Southern Europe
    "MS": "AM",  # Montserrat / region=Americas / subregion=Caribbean
    "MA": "AF",  # Morocco / region=Africa / subregion=Northern Africa
    "MZ": "AF",  # Mozambique / region=Africa / subregion=Eastern Africa
    "MM": "AS",  # Myanmar / region=Asia / subregion=South-Eastern Asia
    "NA": "AF",  # Namibia / region=Africa / subregion=Southern Africa
    "NR": "OC",  # Nauru / region=Oceania / subregion=Micronesia
    "NP": "AS",  # Nepal / region=Asia / subregion=Southern Asia
    "NL": "EU",  # Netherlands / region=Europe / subregion=Western Europe
    "NC": "OC",  # New Caledonia / region=Oceania / subregion=Melanesia
    "NZ": "OC",  # New Zealand / region=Oceania / subregion=Australia and New Zealand
    "NI": "AM",  # Nicaragua / region=Americas / subregion=Central America
    "NE": "AF",  # Niger / region=Africa / subregion=Western Africa
    "NG": "AF",  # Nigeria / region=Africa / subregion=Western Africa
    "NU": "OC",  # Niue / region=Oceania / subregion=Polynesia
    "NF": "OC",  # Norfolk Island / region=Oceania / subregion=Australia and New Zealand
    "KP": "AS",  # North Korea / region=Asia / subregion=Eastern Asia
    "MP": "OC",  # Northern Mariana Islands / region=Oceania / subregion=Micronesia
    "NO": "EU",  # Norway / region=Europe / subregion=Northern Europe
    "OM": "AS",  # Oman / region=Asia / subregion=Western Asia
    "PK": "AS",  # Pakistan / region=Asia / subregion=Southern Asia
    "PW": "OC",  # Palau / region=Oceania / subregion=Micronesia
    "PS": "AS",  # Palestine / region=Asia / subregion=Western Asia
    "PA": "AM",  # Panama / region=Americas / subregion=Central America
    "PG": "OC",  # Papua New Guinea / region=Oceania / subregion=Melanesia
    "PY": "AM",  # Paraguay / region=Americas / subregion=South America
    "PE": "AM",  # Peru / region=Americas / subregion=South America
    "PH": "AS",  # Philippines / region=Asia / subregion=South-Eastern Asia
    "PN": "OC",  # Pitcairn / region=Oceania / subregion=Polynesia
    "PL": "EU",  # Poland / region=Europe / subregion=Eastern Europe
    "PT": "EU",  # Portugal / region=Europe / subregion=Southern Europe
    "PR": "AM",  # Puerto Rico / region=Americas / subregion=Caribbean
    "QA": "AS",  # Qatar / region=Asia / subregion=Western Asia
    "XK": "EU",  # Kosovo / region=Europe / subregion=Eastern Europe
    "RE": "AF",  # Réunion / region=Africa / subregion=Eastern Africa
    "RO": "EU",  # Romania / region=Europe / subregion=Eastern Europe
    "RU": "EU",  # Russia / region=Europe / subregion=Eastern Europe
    "RW": "AF",  # Rwanda / region=Africa / subregion=Eastern Africa
    "BL": "AM",  # Saint Barthélemy / region=Americas / subregion=Caribbean
    "SH": "AF",  # Saint Helena / region=Africa / subregion=Western Africa
    "KN": "AM",  # Saint Kitts and Nevis / region=Americas / subregion=Caribbean
    "LC": "AM",  # Saint Lucia / region=Americas / subregion=Caribbean
    "MF": "AM",  # Saint Martin / region=Americas / subregion=Caribbean
    "PM": "AM",  # Saint Pierre / region=Americas / subregion=Northern America
    "VC": "AM",  # Saint Vincent / region=Americas / subregion=Caribbean
    "WS": "OC",  # Samoa / region=Oceania / subregion=Polynesia
    "SM": "EU",  # San Marino / region=Europe / subregion=Southern Europe
    "ST": "AF",  # Sao Tome / region=Africa / subregion=Middle Africa
    "SA": "AS",  # Saudi Arabia / region=Asia / subregion=Western Asia
    "SN": "AF",  # Senegal / region=Africa / subregion=Western Africa
    "RS": "EU",  # Serbia / region=Europe / subregion=Southern Europe
    "SC": "AF",  # Seychelles / region=Africa / subregion=Eastern Africa
    "SL": "AF",  # Sierra Leone / region=Africa / subregion=Western Africa
    "SG": "AS",  # Singapore / region=Asia / subregion=South-Eastern Asia
    "SX": "AM",  # Sint Maarten / region=Americas / subregion=Caribbean
    "SK": "EU",  # Slovakia / region=Europe / subregion=Eastern Europe
    "SI": "EU",  # Slovenia / region=Europe / subregion=Southern Europe
    "SB": "OC",  # Solomon Islands / region=Oceania / subregion=Melanesia
    "SO": "AF",  # Somalia / region=Africa / subregion=Eastern Africa
    "ZA": "AF",  # South Africa / region=Africa / subregion=Southern Africa
    "GS": "AM",  # South Georgia / region=Americas / subregion=South America
    "KR": "AS",  # South Korea / region=Asia / subregion=Eastern Asia
    "SS": "AF",  # South Sudan / region=Africa / subregion=Middle Africa
    "ES": "EU",  # Spain / region=Europe / subregion=Southern Europe
    "LK": "AS",  # Sri Lanka / region=Asia / subregion=Southern Asia
    "SD": "AF",  # Sudan / region=Africa / subregion=Northern Africa
    "SR": "AM",  # Suriname / region=Americas / subregion=South America
    "SJ": "EU",  # Svalbard / region=Europe / subregion=Northern Europe
    "SZ": "AF",  # Swaziland / region=Africa / subregion=Southern Africa
    "SE": "EU",  # Sweden / region=Europe / subregion=Northern Europe
    "CH": "EU",  # Switzerland / region=Europe / subregion=Western Europe
    "SY": "AS",  # Syria / region=Asia / subregion=Western Asia
    "TW": "AS",  # Taiwan / region=Asia / subregion=Eastern Asia
    "TJ": "AS",  # Tajikistan / region=Asia / subregion=Central Asia
    "TZ": "AF",  # Tanzania / region=Africa / subregion=Eastern Africa
    "TH": "AS",  # Thailand / region=Asia / subregion=South-Eastern Asia
    "TL": "AS",  # Timor-Leste / region=Asia / subregion=South-Eastern Asia
    "TG": "AF",  # Togo / region=Africa / subregion=Western Africa
    "TK": "OC",  # Tokelau / region=Oceania / subregion=Polynesia
    "TO": "OC",  # Tonga / region=Oceania / subregion=Polynesia
    "TT": "AM",  # Trinidad and Tobago / region=Americas / subregion=Caribbean
    "TN": "AF",  # Tunisia / region=Africa / subregion=Northern Africa
    "TR": "AS",  # Turkey / region=Asia / subregion=Western Asia
    "TM": "AS",  # Turkmenistan / region=Asia / subregion=Central Asia
    "TC": "AM",  # Turks and Caicos / region=Americas / subregion=Caribbean
    "TV": "OC",  # Tuvalu / region=Oceania / subregion=Polynesia
    "UG": "AF",  # Uganda / region=Africa / subregion=Eastern Africa
    "UA": "EU",  # Ukraine / region=Europe / subregion=Eastern Europe
    "AE": "AS",  # United Arab Emirates / region=Asia / subregion=Western Asia
    "GB": "EU",  # United Kingdom / region=Europe / subregion=Northern Europe
    "US": "AM",  # United States / region=Americas / subregion=Northern America
    "UY": "AM",  # Uruguay / region=Americas / subregion=South America
    "UZ": "AS",  # Uzbekistan / region=Asia / subregion=Central Asia
    "VU": "OC",  # Vanuatu / region=Oceania / subregion=Melanesia
    "VE": "AM",  # Venezuela / region=Americas / subregion=South America
    "VN": "AS",  # Viet Nam / region=Asia / subregion=South-Eastern Asia
    "WF": "OC",  # Wallis and Futuna / region=Oceania / subregion=Polynesia
    "EH": "AF",  # Western Sahara / region=Africa / subregion=Northern Africa
    "YE": "AS",  # Yemen / region=Asia / subregion=Western Asia
    "ZM": "AF",  # Zambia / region=Africa / subregion=Eastern Africa
    "ZW": "AF",  # Zimbabwe / region=Africa / subregion=Eastern Africa
}

_region_code_to_name_map = {
    "AM": "Americas",
    "AF": "Africa",
    "EU": "Europe",
    "AS": "Asia",
    "OC": "Oceania",
}

ALL_REGIONS = [Region(key, value) for key, value in _region_code_to_name_map]

def get_region_name(region_code: str):
    return _region_code_to_name_map.get(region_code)


def get_region_code(country_code: str):
    if country_code in _region_by_country_code_map:
        return _region_by_country_code_map[country_code]
    else:
        return "Undefined"
    
# fmt: off
_all_sepa_euro_country_codes = {"AT", "BE", "CY", "DE", "EE", "FI", "FR", "GR", "IE",
                                "IT", "LV", "LT", "LU", "MC", "MT", "NL", "PT", "SK", "SI", "ES", "AD", "SM", "VA"}

_all_sepa_non_euro_country_codes = {"BG", "HR", "CZ", "DK", "GB", "HU", "PL", "RO",
                "SE", "IS", "NO", "LI", "CH", "JE", "GI"}

_all_revolut_country_codes = {"AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
                            "DE", "GR", "HU", "IS", "IE", "IT", "LV", "LI", "LT", "LU", "MT", "NL",
                            "NO", "PL", "PT", "RO", "SK", "SI", "ES", "SE", "GB",
                            "AU", "CA", "SG", "CH", "US"}

_all_amazon_gift_card_country_codes = {"AU", "CA", "FR", "DE", "IT", "NL", "ES", "GB", "IN", "JP",
                "SA", "SE", "SG", "TR", "US"}
# fmt: on


ALL_COUNTRIES: List[Country] = list()
ALL_COUNTRIES_BY_CODE: Dict[str, Country] = dict()
ALL_SEPA_EURO_COUNTRIES: List[Country] = list()
ALL_SEPA_NONE_EURO_COUNTRIES: List[Country] = list()
ALL_SEPA_COUNTRIES: List[Country] = list()
ALL_REVOLUT_COUNTRIES: List[Country] = list()
ALL_AMAZON_GIFT_CARD_COUNTRIES: List[Country] = list()

for locale in ALL_LOCALES:
    region_code = get_region_code(locale.country)
    region = Region(region_code, get_region_name(region_code))
    country = Country(locale.country, locale.display_country, region)
    ALL_COUNTRIES.append(country)
    ALL_COUNTRIES_BY_CODE[locale.country] = country
    if locale.country in _all_sepa_euro_country_codes:
        ALL_SEPA_EURO_COUNTRIES.append(country)
    if locale.country in _all_sepa_non_euro_country_codes:
        ALL_SEPA_NONE_EURO_COUNTRIES.append(country)
    if locale.country in _all_revolut_country_codes:
        ALL_REVOLUT_COUNTRIES.append(country)
    if locale.country in _all_amazon_gift_card_country_codes:
        ALL_AMAZON_GIFT_CARD_COUNTRIES.append(country)
        
ALL_SEPA_COUNTRIES = ALL_SEPA_EURO_COUNTRIES + ALL_SEPA_NONE_EURO_COUNTRIES

ALL_SEPA_EURO_COUNTRIES.sort(key=lambda e: e.name)
ALL_SEPA_NONE_EURO_COUNTRIES.sort(key=lambda e: e.name)
ALL_REVOLUT_COUNTRIES.sort(key=lambda e: e.name)
ALL_AMAZON_GIFT_CARD_COUNTRIES.sort(key=lambda e: e.name)
ALL_SEPA_COUNTRIES.sort(key=lambda e: e.name)


def find_country_by_code(country_code: str) -> Optional[Country]:
    return ALL_COUNTRIES_BY_CODE.get(country_code)

def get_all_sepa_countries():
    return ALL_SEPA_COUNTRIES

    
