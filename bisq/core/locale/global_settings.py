
from typing import TYPE_CHECKING, Optional
from bisq.core.locale.language_util import LanguageUtil
from utils.data import SimpleProperty

if TYPE_CHECKING:
    from bisq.core.locale.trade_currency import TradeCurrency

class GlobalSettings:
    use_animations = True
    locale_property = SimpleProperty(LanguageUtil.get_default_language())
    default_trade_currency: Optional["TradeCurrency"] = None
    btc_denomination: Optional[str] = None
