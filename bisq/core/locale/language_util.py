

from bisq.core.locale.babel_min import default_locale
from bisq.core.locale.locale_util import ALL_LANGUAGE_CODES, ALL_LOCALES

# TODO: complete ?
class LanguageUtil:
    @staticmethod
    def get_default_language():
        locale = default_locale()
        language, country = locale[0], locale[1]
        locale = None
        # first check if the locale is in ALL_LOCALES by comparing the first element in the tuple with LocaleData.language,
        # if true, checks the second element in the tuple with LocaleData.country, if also true returns
        # otherwise continues search while taking note of the first match
        # if no exact match is found, the first one that first element in the tuple matches LocaleData.language is returned
        for locale_data in ALL_LOCALES:
            if locale_data.language == language:
                if locale_data.country == country:
                    return locale_data
                if not locale:
                    locale = locale_data
        return locale
    
    user_language_codes = [
        "en",
    ]

    rtl_language_codes = [
        "fa", # Persian
        "ar", # Arabic
        "iw", # Hebrew
    ]
    
    @staticmethod
    def get_all_language_codes():
        return ALL_LANGUAGE_CODES