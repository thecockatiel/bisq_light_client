from bisq.core.monetary.volume import Volume
from bitcoinj.base.utils.monetary_format import MonetaryFormat

# TODO: incomplete
class VolumeUtil:
    FIAT_VOLUME_FORMAT = MonetaryFormat().with_shift(0).with_min_decimals(0).repeat_optional_decimals(0, 0)
    
    @staticmethod
    def get_rounded_fiat_volume(volume_by_amount: Volume):
        # We want to get rounded to 1 unit of the fiat currency, e.g. 1 EUR.
        return VolumeUtil.get_adjusted_fiat_volume(volume_by_amount.monetary, 1)
    
    @staticmethod
    def get_adjusted_volume_for_hal_cash(volume_by_amount: Volume):
        # EUR has precision 4 and we want multiple of 10 so we divide by 100000 then
        # round and multiply with 10
        return VolumeUtil.get_adjusted_fiat_volume(volume_by_amount.monetary, 10)

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

        
