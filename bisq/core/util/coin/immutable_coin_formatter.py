
from typing import TYPE_CHECKING
from bisq.core.util.coin.coin_formatter import CoinFormatter
from bisq.core.util.formatting_util import FormattingUtils
from bitcoinj.base.coin import Coin

if TYPE_CHECKING:
    from bitcoinj.base.utils.monetary_format import MonetaryFormat


# Not so immutable in python.
class ImmutableCoinFormatter(CoinFormatter):
    def __init__(self, monetary_format: "MonetaryFormat"):
        super().__init__()
        # We don't support localized formatting. Format is always using "." as decimal mark and no grouping separator.
        # Input of "," as decimal mark (like in german locale) will be replaced with ".".
        # Input of a group separator (1,123,45) lead to an validation error.
        # Note: BtcFormat was intended to be used, but it lead to many problems (automatic format to mBit,
        # no way to remove grouping separator). It seems to be not optimal for user input formatting.
        self.monetary_format = monetary_format
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // BTC
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def format_coin(self, coin_or_value, *, append_code=False, decimal_places=-1, decimal_aligned=False, max_number_of_digits=0):
        if isinstance(coin_or_value, int):
            coin_or_value = Coin.value_of(coin_or_value)
        if append_code:
            return self.format_coin_with_code(coin_or_value)
        
        return FormattingUtils.format_coin(coin_or_value, self.monetary_format, decimal_places, decimal_aligned, max_number_of_digits)

    def format_coin_with_code(self, coin_or_value):
        return FormattingUtils.format_coin_with_code(coin_or_value, self.monetary_format)

    def get_monetary_format(self):
        return self.monetary_format