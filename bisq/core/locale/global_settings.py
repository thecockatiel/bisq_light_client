
from typing import TYPE_CHECKING, Optional
from bisq.core.locale.language_util import LanguageUtil
from utils.data import SimpleProperty

if TYPE_CHECKING:
    from bisq.core.locale.trade_currency import TradeCurrency

class GlobalSettings:
    use_animations = True
    locale = LanguageUtil.get_default_language()
    locale_property = SimpleProperty(locale)
    default_trade_currency: Optional["TradeCurrency"]
    btc_denomination: Optional[str]
    
    @staticmethod
    def set_locale(locale):
        GlobalSettings.locale = locale
        GlobalSettings.locale_property.set(locale)
        
    @staticmethod
    def set_use_animations(animations: bool):
        GlobalSettings.use_animations = animations
        
    @staticmethod
    def set_default_trade_currency(currency: "TradeCurrency"):
        GlobalSettings.default_trade_currency = currency
        
    @staticmethod
    def set_btc_denomination(denomination: str):
        GlobalSettings.btc_denomination = denomination