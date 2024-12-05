

from bisq.core.locale.babel_min import default_locale
from bisq.core.locale.locale_util import ALL_LANGUAGE_CODES, LocaleData, find_locale

# TODO: complete ?
class LanguageUtil:
    @staticmethod
    def get_default_language() -> 'LocaleData':
        locale = default_locale() or ("en", "US")
        language, country = locale[0], locale[1]
        return find_locale(language, country)
    
    def get_default_language_locale_as_code() -> str:
        return LanguageUtil.get_default_language().language
    
    def get_english_language_locale_code() -> str:
        return "en" # returned by runing the following code in java: new Locale(Locale.ENGLISH.getLanguage()).getLanguage()
    
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