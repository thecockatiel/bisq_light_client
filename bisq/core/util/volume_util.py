import math
from typing import TYPE_CHECKING
from bisq.core.locale.res import Res
from bisq.core.monetary.volume import Volume
from utils.java.decimal_format import DecimalFormat
from bisq.core.util.formatting_util import FormattingUtils
from bitcoinj.base.utils.fiat import Fiat
from bitcoinj.base.utils.monetary_format import MonetaryFormat

if TYPE_CHECKING:
    from bisq.core.offer.offer import Offer

class VolumeUtil:
    FIAT_VOLUME_FORMAT = MonetaryFormat().with_shift(0).with_min_decimals(0).repeat_optional_decimals(0, 0)
    
    @staticmethod
    def get_rounded_fiat_volume(volume_by_amount: Volume):
        # We want to get rounded to 1 unit of the fiat currency, e.g. 1 EUR.
        return VolumeUtil.get_adjusted_fiat_volume(volume_by_amount, 1)
    
    @staticmethod
    def get_adjusted_volume_for_hal_cash(volume_by_amount: Volume):
        # EUR has precision 4 and we want multiple of 10 so we divide by 100000 then
        # round and multiply with 10
        return VolumeUtil.get_adjusted_fiat_volume(volume_by_amount, 10)

    @staticmethod
    def get_adjusted_fiat_volume(volume_by_amount: Volume, factor: int):
        """
        Args:
            volume_by_amount: The volume generated from an amount
            factor: The factor used for rounding. E.g. 1 means rounded to
                    units of 1 EUR, 10 means rounded to 10 EUR.

        Returns:
            Volume: The adjusted Fiat volume
        """
        # Fiat currencies use precision 4 and we want multiple of factor so we divide by 10000 * factor then
        # round and multiply with factor
        rounded_volume = round(volume_by_amount.monetary.get_value() / (10000 * factor)) * factor
        # Smallest allowed volume is factor (e.g. 10 EUR or 1 EUR,...)
        rounded_volume = max(factor, rounded_volume)
        return Volume.parse(str(rounded_volume), volume_by_amount.currency_code)

    @staticmethod
    def format_offer_volume(offer: "Offer", decimal_aligned: bool, max_number_of_digits: int, show_range: bool = True) -> str:
        formatted_volume = (VolumeUtil.format_volume(offer.min_volume) + FormattingUtils.RANGE_SEPARATOR + VolumeUtil.format_volume(offer.volume)
                            if offer.is_range and show_range
                            else VolumeUtil.format_volume(offer.volume))

        if decimal_aligned:
            formatted_volume = FormattingUtils.fill_up_places_with_empty_strings(formatted_volume, max_number_of_digits)
        
        return formatted_volume
    
    @staticmethod
    def format_large_fiat(value: float, currency: str) -> str:
        if value <= 0:
            return "0"
        number_format = DecimalFormat(grouping_used=True)
        return f"{number_format.format(value)} {currency}"

    @staticmethod
    def format_large_fiat_with_unit_postfix(value: float, currency: str) -> str:
        if value <= 0:
            return "0"
        units = ["", "K", "M", "B"]
        digit_groups = int(math.log10(value) / math.log10(1000))
        # I don't know the reason for this sophisticated format defined here
        # but our simple python implementation seems to yield the same results as this
        formatted_value = DecimalFormat("#,##0.###").format(value / math.pow(1000, digit_groups))
        return f"{formatted_value}{units[digit_groups]} {currency}"

    @staticmethod
    def format_volume(volume: Volume, fiat_volume_format: MonetaryFormat = None, append_currency_code: bool = None) -> str:
        if fiat_volume_format is None:
            fiat_volume_format = VolumeUtil.FIAT_VOLUME_FORMAT
        
        if append_currency_code is None:
            append_currency_code = False

        if volume is not None:
            monetary = volume.monetary
            if isinstance(monetary, Fiat):
                return FormattingUtils.format_fiat(monetary, fiat_volume_format, append_currency_code)
            else:
                return FormattingUtils.format_altcoin_volume(monetary, append_currency_code)
        else:
            return ""
    
    @staticmethod
    def format_volume_with_code(volume: Volume) -> str:
        return VolumeUtil.format_volume(volume, append_currency_code=True)

    @staticmethod
    def format_average_volume_with_code(volume: Volume) -> str:
        fiat_volume_format = VolumeUtil.FIAT_VOLUME_FORMAT.with_min_decimals(2)
        return VolumeUtil.format_volume(volume, fiat_volume_format, True)

    @staticmethod
    def format_volume_label(currency_code: str, postfix: str = "") -> str:
        return Res.get("formatter.formatVolumeLabel", currency_code, postfix)
