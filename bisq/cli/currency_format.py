from decimal import Decimal
from typing import Union
from bisq.core.util.decimal_format import DecimalFormat

# TODO: implement rest and test
class CurrencyFormat:
    """Utility for formatting amounts, volumes and fees;  there is no i18n support in the CLI."""

    INTERNAL_FIAT_DECIMAL_FORMAT = DecimalFormat("##############0.0000")

    SATOSHI_DIVISOR = 100_000_000
    SATOSHI_FORMAT = DecimalFormat("###,##0.00000000")
    BTC_FORMAT = DecimalFormat("###,##0.########")
    BTC_TX_FEE_FORMAT = DecimalFormat("###,###,##0")

    BSQ_SATOSHI_DIVISOR = 100
    BSQ_FORMAT = DecimalFormat("###,###,###,##0.00")

    @staticmethod
    def format_satoshis(sats: Union[str, int]) -> str:
        return CurrencyFormat.SATOSHI_FORMAT.format(
            Decimal(sats) / CurrencyFormat.SATOSHI_DIVISOR
        )

    @staticmethod
    def format_btc(sats: Union[str, int]) -> str:
        return CurrencyFormat.BTC_FORMAT.format(
            Decimal(sats) / CurrencyFormat.SATOSHI_DIVISOR
        )

    @staticmethod
    def format_bsq(sats: Union[str, int]) -> str:
        return CurrencyFormat.BSQ_FORMAT.format(
            Decimal(sats) / CurrencyFormat.BSQ_SATOSHI_DIVISOR
        )
