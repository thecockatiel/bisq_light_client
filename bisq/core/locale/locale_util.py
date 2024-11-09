from dataclasses import dataclass

# This file contains data exported from java bisq project by printing needed data from the list inside LanguageUtil and using Locale class
# NOTE: I am aware that this limited implementation is limited to English, and that's fine for now, at least.

@dataclass(frozen=True)
class LocaleData():
    language: str
    display_language: str
    country: str
    display_country: str

ALL_LOCALES = {
    LocaleData('ps', 'Pashto', 'AF', 'Afghanistan'),
    LocaleData('sv', 'Swedish', 'AX', 'Åland Islands'),
    LocaleData('sq', 'Albanian', 'AL', 'Albania'),
    LocaleData('ar', 'Arabic', 'DZ', 'Algeria'),
    LocaleData('en', 'English', 'AS', 'American Samoa'),
    LocaleData('ca', 'Catalan', 'AD', 'Andorra'),
    LocaleData('pt', 'Portuguese', 'AO', 'Angola'),
    LocaleData('en', 'English', 'AI', 'Anguilla'),
    LocaleData('en', 'English', 'AG', 'Antigua & Barbuda'),
    LocaleData('es', 'Spanish', 'AR', 'Argentina'),
    LocaleData('hy', 'Armenian', 'AM', 'Armenia'),
    LocaleData('nl', 'Dutch', 'AW', 'Aruba'),
    LocaleData('en', 'English', 'AU', 'Australia'),
    LocaleData('de', 'German', 'AT', 'Austria'),
    LocaleData('az', 'Azerbaijani', 'AZ', 'Azerbaijan'),
    LocaleData('en', 'English', 'BS', 'Bahamas'),
    LocaleData('ar', 'Arabic', 'BH', 'Bahrain'),
    LocaleData('bn', 'Bangla', 'BD', 'Bangladesh'),
    LocaleData('en', 'English', 'BB', 'Barbados'),
    LocaleData('be', 'Belarusian', 'BY', 'Belarus'),
    LocaleData('nl', 'Dutch', 'BE', 'Belgium'),
    LocaleData('en', 'English', 'BZ', 'Belize'),
    LocaleData('fr', 'French', 'BJ', 'Benin'),
    LocaleData('en', 'English', 'BM', 'Bermuda'),
    LocaleData('dz', 'Dzongkha', 'BT', 'Bhutan'),
    LocaleData('es', 'Spanish', 'BO', 'Bolivia'),
    LocaleData('nl', 'Dutch', 'BQ', 'Caribbean Netherlands'),
    LocaleData('bs', 'Bosnian', 'BA', 'Bosnia & Herzegovina'),
    LocaleData('en', 'English', 'BW', 'Botswana'),
    LocaleData('pt', 'Portuguese', 'BR', 'Brazil'),
    LocaleData('en', 'English', 'IO', 'British Indian Ocean Territory'),
    LocaleData('en', 'English', 'UM', 'U.S. Outlying Islands'),
    LocaleData('en', 'English', 'VG', 'British Virgin Islands'),
    LocaleData('en', 'English', 'VI', 'U.S. Virgin Islands'),
    LocaleData('ms', 'Malay', 'BN', 'Brunei'),
    LocaleData('bg', 'Bulgarian', 'BG', 'Bulgaria'),
    LocaleData('fr', 'French', 'BF', 'Burkina Faso'),
    LocaleData('fr', 'French', 'BI', 'Burundi'),
    LocaleData('km', 'Khmer', 'KH', 'Cambodia'),
    LocaleData('en', 'English', 'CM', 'Cameroon'),
    LocaleData('en', 'English', 'CA', 'Canada'),
    LocaleData('pt', 'Portuguese', 'CV', 'Cape Verde'),
    LocaleData('en', 'English', 'KY', 'Cayman Islands'),
    LocaleData('fr', 'French', 'CF', 'Central African Republic'),
    LocaleData('fr', 'French', 'TD', 'Chad'),
    LocaleData('es', 'Spanish', 'CL', 'Chile'),
    LocaleData('zh', 'Chinese', 'CN', 'China'),
    LocaleData('en', 'English', 'CX', 'Christmas Island'),
    LocaleData('en', 'English', 'CC', 'Cocos (Keeling) Islands'),
    LocaleData('es', 'Spanish', 'CO', 'Colombia'),
    LocaleData('ar', 'Arabic', 'KM', 'Comoros'),
    LocaleData('fr', 'French', 'CG', 'Congo - Brazzaville'),
    LocaleData('fr', 'French', 'CD', 'Congo - Kinshasa'),
    LocaleData('en', 'English', 'CK', 'Cook Islands'),
    LocaleData('es', 'Spanish', 'CR', 'Costa Rica'),
    LocaleData('hr', 'Croatian', 'HR', 'Croatia'),
    LocaleData('es', 'Spanish', 'CU', 'Cuba'),
    LocaleData('nl', 'Dutch', 'CW', 'Curaçao'),
    LocaleData('el', 'Greek', 'CY', 'Cyprus'),
    LocaleData('cs', 'Czech', 'CZ', 'Czechia'),
    LocaleData('da', 'Danish', 'DK', 'Denmark'),
    LocaleData('fr', 'French', 'DJ', 'Djibouti'),
    LocaleData('en', 'English', 'DM', 'Dominica'),
    LocaleData('es', 'Spanish', 'DO', 'Dominican Republic'),
    LocaleData('es', 'Spanish', 'EC', 'Ecuador'),
    LocaleData('ar', 'Arabic', 'EG', 'Egypt'),
    LocaleData('es', 'Spanish', 'SV', 'El Salvador'),
    LocaleData('es', 'Spanish', 'GQ', 'Equatorial Guinea'),
    LocaleData('ti', 'Tigrinya', 'ER', 'Eritrea'),
    LocaleData('et', 'Estonian', 'EE', 'Estonia'),
    LocaleData('am', 'Amharic', 'ET', 'Ethiopia'),
    LocaleData('en', 'English', 'FK', 'Falkland Islands'),
    LocaleData('fo', 'Faroese', 'FO', 'Faroe Islands'),
    LocaleData('en', 'English', 'FJ', 'Fiji'),
    LocaleData('fi', 'Finnish', 'FI', 'Finland'),
    LocaleData('fr', 'French', 'FR', 'France'),
    LocaleData('fr', 'French', 'GF', 'French Guiana'),
    LocaleData('fr', 'French', 'PF', 'French Polynesia'),
    LocaleData('fr', 'French', 'TF', 'French Southern Territories'),
    LocaleData('fr', 'French', 'GA', 'Gabon'),
    LocaleData('en', 'English', 'GM', 'Gambia'),
    LocaleData('ka', 'Georgian', 'GE', 'Georgia'),
    LocaleData('de', 'German', 'DE', 'Germany'),
    LocaleData('en', 'English', 'GH', 'Ghana'),
    LocaleData('en', 'English', 'GI', 'Gibraltar'),
    LocaleData('el', 'Greek', 'GR', 'Greece'),
    LocaleData('kl', 'Kalaallisut', 'GL', 'Greenland'),
    LocaleData('en', 'English', 'GD', 'Grenada'),
    LocaleData('fr', 'French', 'GP', 'Guadeloupe'),
    LocaleData('en', 'English', 'GU', 'Guam'),
    LocaleData('es', 'Spanish', 'GT', 'Guatemala'),
    LocaleData('en', 'English', 'GG', 'Guernsey'),
    LocaleData('fr', 'French', 'GN', 'Guinea'),
    LocaleData('pt', 'Portuguese', 'GW', 'Guinea-Bissau'),
    LocaleData('en', 'English', 'GY', 'Guyana'),
    LocaleData('fr', 'French', 'HT', 'Haiti'),
    LocaleData('la', 'Latin', 'VA', 'Vatican City'),
    LocaleData('es', 'Spanish', 'HN', 'Honduras'),
    LocaleData('en', 'English', 'HK', 'Hong Kong SAR China'),
    LocaleData('hu', 'Hungarian', 'HU', 'Hungary'),
    LocaleData('is', 'Icelandic', 'IS', 'Iceland'),
    LocaleData('hi', 'Hindi', 'IN', 'India'),
    LocaleData('id', 'Indonesian', 'ID', 'Indonesia'),
    LocaleData('fr', 'French', 'CI', 'Côte d’Ivoire'),
    LocaleData('fa', 'Persian', 'IR', 'Iran'),
    LocaleData('ar', 'Arabic', 'IQ', 'Iraq'),
    LocaleData('ga', 'Irish', 'IE', 'Ireland'),
    LocaleData('en', 'English', 'IM', 'Isle of Man'),
    LocaleData('he', 'Hebrew', 'IL', 'Israel'),
    LocaleData('it', 'Italian', 'IT', 'Italy'),
    LocaleData('en', 'English', 'JM', 'Jamaica'),
    LocaleData('ja', 'Japanese', 'JP', 'Japan'),
    LocaleData('en', 'English', 'JE', 'Jersey'),
    LocaleData('ar', 'Arabic', 'JO', 'Jordan'),
    LocaleData('kk', 'Kazakh', 'KZ', 'Kazakhstan'),
    LocaleData('en', 'English', 'KE', 'Kenya'),
    LocaleData('en', 'English', 'KI', 'Kiribati'),
    LocaleData('ar', 'Arabic', 'KW', 'Kuwait'),
    LocaleData('ky', 'Kyrgyz', 'KG', 'Kyrgyzstan'),
    LocaleData('lo', 'Lao', 'LA', 'Laos'),
    LocaleData('lv', 'Latvian', 'LV', 'Latvia'),
    LocaleData('ar', 'Arabic', 'LB', 'Lebanon'),
    LocaleData('en', 'English', 'LS', 'Lesotho'),
    LocaleData('en', 'English', 'LR', 'Liberia'),
    LocaleData('ar', 'Arabic', 'LY', 'Libya'),
    LocaleData('de', 'German', 'LI', 'Liechtenstein'),
    LocaleData('lt', 'Lithuanian', 'LT', 'Lithuania'),
    LocaleData('fr', 'French', 'LU', 'Luxembourg'),
    LocaleData('zh', 'Chinese', 'MO', 'Macao SAR China'),
    LocaleData('mk', 'Macedonian', 'MK', 'North Macedonia'),
    LocaleData('fr', 'French', 'MG', 'Madagascar'),
    LocaleData('en', 'English', 'MW', 'Malawi'),
    LocaleData('en', 'English', 'MY', 'Malaysia'),
    LocaleData('dv', 'Divehi', 'MV', 'Maldives'),
    LocaleData('fr', 'French', 'ML', 'Mali'),
    LocaleData('mt', 'Maltese', 'MT', 'Malta'),
    LocaleData('en', 'English', 'MH', 'Marshall Islands'),
    LocaleData('fr', 'French', 'MQ', 'Martinique'),
    LocaleData('ar', 'Arabic', 'MR', 'Mauritania'),
    LocaleData('en', 'English', 'MU', 'Mauritius'),
    LocaleData('fr', 'French', 'YT', 'Mayotte'),
    LocaleData('es', 'Spanish', 'MX', 'Mexico'),
    LocaleData('en', 'English', 'FM', 'Micronesia'),
    LocaleData('ro', 'Romanian', 'MD', 'Moldova'),
    LocaleData('fr', 'French', 'MC', 'Monaco'),
    LocaleData('mn', 'Mongolian', 'MN', 'Mongolia'),
    LocaleData('sr', 'Serbian', 'ME', 'Montenegro'),
    LocaleData('en', 'English', 'MS', 'Montserrat'),
    LocaleData('ar', 'Arabic', 'MA', 'Morocco'),
    LocaleData('pt', 'Portuguese', 'MZ', 'Mozambique'),
    LocaleData('my', 'Burmese', 'MM', 'Myanmar (Burma)'),
    LocaleData('en', 'English', 'NA', 'Namibia'),
    LocaleData('en', 'English', 'NR', 'Nauru'),
    LocaleData('ne', 'Nepali', 'NP', 'Nepal'),
    LocaleData('nl', 'Dutch', 'NL', 'Netherlands'),
    LocaleData('fr', 'French', 'NC', 'New Caledonia'),
    LocaleData('en', 'English', 'NZ', 'New Zealand'),
    LocaleData('es', 'Spanish', 'NI', 'Nicaragua'),
    LocaleData('fr', 'French', 'NE', 'Niger'),
    LocaleData('en', 'English', 'NG', 'Nigeria'),
    LocaleData('en', 'English', 'NU', 'Niue'),
    LocaleData('en', 'English', 'NF', 'Norfolk Island'),
    LocaleData('ko', 'Korean', 'KP', 'North Korea'),
    LocaleData('en', 'English', 'MP', 'Northern Mariana Islands'),
    LocaleData('no', 'Norwegian', 'NO', 'Norway'),
    LocaleData('ar', 'Arabic', 'OM', 'Oman'),
    LocaleData('en', 'English', 'PK', 'Pakistan'),
    LocaleData('en', 'English', 'PW', 'Palau'),
    LocaleData('ar', 'Arabic', 'PS', 'Palestinian Territories'),
    LocaleData('es', 'Spanish', 'PA', 'Panama'),
    LocaleData('en', 'English', 'PG', 'Papua New Guinea'),
    LocaleData('es', 'Spanish', 'PY', 'Paraguay'),
    LocaleData('es', 'Spanish', 'PE', 'Peru'),
    LocaleData('en', 'English', 'PH', 'Philippines'),
    LocaleData('en', 'English', 'PN', 'Pitcairn Islands'),
    LocaleData('pl', 'Polish', 'PL', 'Poland'),
    LocaleData('pt', 'Portuguese', 'PT', 'Portugal'),
    LocaleData('es', 'Spanish', 'PR', 'Puerto Rico'),
    LocaleData('ar', 'Arabic', 'QA', 'Qatar'),
    LocaleData('sq', 'Albanian', 'XK', 'Kosovo'),
    LocaleData('fr', 'French', 'RE', 'Réunion'),
    LocaleData('ro', 'Romanian', 'RO', 'Romania'),
    LocaleData('ru', 'Russian', 'RU', 'Russia'),
    LocaleData('rw', 'Kinyarwanda', 'RW', 'Rwanda'),
    LocaleData('fr', 'French', 'BL', 'St. Barthélemy'),
    LocaleData('en', 'English', 'SH', 'St. Helena'),
    LocaleData('en', 'English', 'KN', 'St. Kitts & Nevis'),
    LocaleData('en', 'English', 'LC', 'St. Lucia'),
    LocaleData('en', 'English', 'MF', 'St. Martin'),
    LocaleData('fr', 'French', 'PM', 'St. Pierre & Miquelon'),
    LocaleData('en', 'English', 'VC', 'St. Vincent & Grenadines'),
    LocaleData('sm', 'Samoan', 'WS', 'Samoa'),
    LocaleData('it', 'Italian', 'SM', 'San Marino'),
    LocaleData('pt', 'Portuguese', 'ST', 'São Tomé & Príncipe'),
    LocaleData('ar', 'Arabic', 'SA', 'Saudi Arabia'),
    LocaleData('fr', 'French', 'SN', 'Senegal'),
    LocaleData('sr', 'Serbian', 'RS', 'Serbia'),
    LocaleData('fr', 'French', 'SC', 'Seychelles'),
    LocaleData('en', 'English', 'SL', 'Sierra Leone'),
    LocaleData('en', 'English', 'SG', 'Singapore'),
    LocaleData('nl', 'Dutch', 'SX', 'Sint Maarten'),
    LocaleData('sk', 'Slovak', 'SK', 'Slovakia'),
    LocaleData('sl', 'Slovenian', 'SI', 'Slovenia'),
    LocaleData('en', 'English', 'SB', 'Solomon Islands'),
    LocaleData('so', 'Somali', 'SO', 'Somalia'),
    LocaleData('af', 'Afrikaans', 'ZA', 'South Africa'),
    LocaleData('en', 'English', 'GS', 'South Georgia & South Sandwich Islands'),
    LocaleData('ko', 'Korean', 'KR', 'South Korea'),
    LocaleData('en', 'English', 'SS', 'South Sudan'),
    LocaleData('es', 'Spanish', 'ES', 'Spain'),
    LocaleData('si', 'Sinhala', 'LK', 'Sri Lanka'),
    LocaleData('ar', 'Arabic', 'SD', 'Sudan'),
    LocaleData('nl', 'Dutch', 'SR', 'Suriname'),
    LocaleData('no', 'Norwegian', 'SJ', 'Svalbard & Jan Mayen'),
    LocaleData('en', 'English', 'SZ', 'Eswatini'),
    LocaleData('sv', 'Swedish', 'SE', 'Sweden'),
    LocaleData('de', 'German', 'CH', 'Switzerland'),
    LocaleData('ar', 'Arabic', 'SY', 'Syria'),
    LocaleData('zh', 'Chinese', 'TW', 'Taiwan'),
    LocaleData('tg', 'Tajik', 'TJ', 'Tajikistan'),
    LocaleData('sw', 'Swahili', 'TZ', 'Tanzania'),
    LocaleData('th', 'Thai', 'TH', 'Thailand'),
    LocaleData('pt', 'Portuguese', 'TL', 'Timor-Leste'),
    LocaleData('fr', 'French', 'TG', 'Togo'),
    LocaleData('en', 'English', 'TK', 'Tokelau'),
    LocaleData('en', 'English', 'TO', 'Tonga'),
    LocaleData('en', 'English', 'TT', 'Trinidad & Tobago'),
    LocaleData('ar', 'Arabic', 'TN', 'Tunisia'),
    LocaleData('tr', 'Turkish', 'TR', 'Turkey'),
    LocaleData('tk', 'Turkmen', 'TM', 'Turkmenistan'),
    LocaleData('en', 'English', 'TC', 'Turks & Caicos Islands'),
    LocaleData('en', 'English', 'TV', 'Tuvalu'),
    LocaleData('en', 'English', 'UG', 'Uganda'),
    LocaleData('uk', 'Ukrainian', 'UA', 'Ukraine'),
    LocaleData('ar', 'Arabic', 'AE', 'United Arab Emirates'),
    LocaleData('en', 'English', 'GB', 'United Kingdom'),
    LocaleData('en', 'English', 'US', 'United States'),
    LocaleData('es', 'Spanish', 'UY', 'Uruguay'),
    LocaleData('uz', 'Uzbek', 'UZ', 'Uzbekistan'),
    LocaleData('bi', 'Bislama', 'VU', 'Vanuatu'),
    LocaleData('es', 'Spanish', 'VE', 'Venezuela'),
    LocaleData('vi', 'Vietnamese', 'VN', 'Vietnam'),
    LocaleData('fr', 'French', 'WF', 'Wallis & Futuna'),
    LocaleData('es', 'Spanish', 'EH', 'Western Sahara'),
    LocaleData('ar', 'Arabic', 'YE', 'Yemen'),
    LocaleData('en', 'English', 'ZM', 'Zambia'),
    LocaleData('en', 'English', 'ZW', 'Zimbabwe')
}

ALL_LANGUAGE_CODES = {"af", "bi", "de", "dv", "en", "ga", "id", "rw", "sw", "la", "mt", "ms", "nl", "sm", "so", "vi", "tr", "az", "bs", "ca", "da", "et", "es", "fr", "fo", "hr", "it", "kl", "lv", "lt", "hu", "no", "uz", "pl", "pt", "ro", "sq", "sk", "sl", "fi", "sv", "tk", "is", "cs", "el", "be", "bg", "ky", "mk", "mn", "ru", "sr", "tg", "uk", "kk", "hy", "he", "ar", "fa", "ps", "ne", "hi", "bn", "si", "th", "lo", "dz", "my", "ka", "ti", "am", "km", "zh", "ja", "ko"}