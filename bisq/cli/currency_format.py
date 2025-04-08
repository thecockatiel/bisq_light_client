from decimal import ROUND_HALF_UP, Decimal
from typing import Union
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from utils.java.decimal_format import DecimalFormat
import grpc_pb2


class CurrencyFormat:
    """Utility for formatting amounts, volumes and fees;  there is no i18n support in the CLI."""

    # Formats numbers for internal use, i.e., grpc request parameters.
    INTERNAL_FIAT_DECIMAL_FORMAT = DecimalFormat("##############0.0000")

    SATOSHI_DIVISOR = 100_000_000
    SATOSHI_FORMAT = DecimalFormat("###,##0.00000000")
    BTC_FORMAT = DecimalFormat("###,##0.########")
    BTC_TX_FEE_FORMAT = DecimalFormat("###,###,##0")

    BSQ_SATOSHI_DIVISOR = 100
    BSQ_FORMAT = DecimalFormat("###,###,###,##0.00")
    VOLUME_FORMAT = DecimalFormat(
        "###",
        rounding=ROUND_HALF_UP,
        grouping_used=True,
    ).set_maximum_fraction_digits(0)
    PRICE_FORMAT = DecimalFormat("###,###.0000")

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

    @staticmethod
    def format_tx_fee_rate_info(tx_fee_rate_info: grpc_pb2.TxFeeRateInfo) -> str:
        if tx_fee_rate_info.use_custom_tx_fee_rate:
            return (
                f"custom tx fee rate: {CurrencyFormat.format_fee_satoshis(tx_fee_rate_info.custom_tx_fee_rate)} sats/byte, "
                f"network rate: {CurrencyFormat.format_fee_satoshis(tx_fee_rate_info.fee_service_rate)} sats/byte, "
                f"min network rate: {CurrencyFormat.format_fee_satoshis(tx_fee_rate_info.min_fee_service_rate)} sats/byte"
            )
        else:
            return (
                f"tx fee rate: {CurrencyFormat.format_fee_satoshis(tx_fee_rate_info.fee_service_rate)} sats/byte, "
                f"min tx fee rate: {CurrencyFormat.format_fee_satoshis(tx_fee_rate_info.min_fee_service_rate)} sats/byte"
            )

    @staticmethod
    def format_internal_fiat_price(price: Union[str, int]) -> str:
        return CurrencyFormat.INTERNAL_FIAT_DECIMAL_FORMAT.format(Decimal(price))

    @staticmethod
    def format_price(price: Union[str, int]) -> str:
        return CurrencyFormat.PRICE_FORMAT.format(Decimal(price) / 10_000)

    @staticmethod
    def format_fiat_volume(volume: Union[str, int]) -> str:
        return CurrencyFormat.VOLUME_FORMAT.format(Decimal(volume) / 10_000)

    @staticmethod
    def to_satoshis(btc: str) -> int:
        if btc.startswith("-"):
            raise IllegalArgumentException(f"'{btc}' is not a positive number")

        try:
            return int(Decimal(btc) * CurrencyFormat.SATOSHI_DIVISOR)
        except Exception as e:
            raise IllegalArgumentException(f"'{btc}' is not a number")

    @staticmethod
    def format_fee_satoshis(sats: Union[str, int]) -> str:
        return CurrencyFormat.BTC_TX_FEE_FORMAT.format(sats)
