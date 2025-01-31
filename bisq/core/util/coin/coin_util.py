from typing import Optional
from decimal import Decimal
from bisq.common.util.math_utils import MathUtils
from bisq.core.btc.wallet.restrictions import Restrictions
from bisq.core.provider.fee.fee_service import FeeService
from bisq.core.util.volume_util import VolumeUtil
from bitcoinj.base.coin import Coin 
from bisq.core.monetary.price import Price
from bisq.core.monetary.volume import Volume
from utils.preconditions import check_argument 


class CoinUtil:

    @staticmethod
    def get_fee_per_btc(fee_per_btc: Optional[Coin], amount: Optional[Coin]) -> Coin:
        """Calculate fee per BTC for a given amount."""
        fee_per_btc = fee_per_btc.value if fee_per_btc else 0
        amount_value = amount.value if amount else 0
        btc_value = Coin.COIN().value
        fact = amount_value / btc_value
        return Coin.value_of(round(fee_per_btc * fact))

    @staticmethod
    def min_coin(a: Coin, b: Coin) -> Coin:
        return a if a <= b else b

    @staticmethod
    def max_coin(a: Coin, b: Coin) -> Coin:
        return a if a >= b else b

    @staticmethod
    def get_fee_per_vbyte(mining_fee: Optional[Coin], tx_vsize: int) -> float:
        value = mining_fee.value if mining_fee else 0
        return MathUtils.round_double((value / tx_vsize), 2)

    @staticmethod
    def get_as_percent_per_btc(value: Optional[Coin], total: Optional[Coin] = None) -> float:
        """
        Convert BTC amount to percent value.
        
        Args:
            value: BTC amount to convert to percent (e.g. 0.01 BTC is 1% of 1 BTC)
            total: Total Btc amount the percentage part is calculated from (Defaults to 1 BTC)
        Returns:
            Percentage as float (e.g. 0.01 for 1%)
        """
        total = total or Coin.COIN()
        value_as_float = value.value if value else 0
        btc_value = total.value if total else 1
        return MathUtils.round_double(value_as_float / btc_value, 4)

    @staticmethod
    def get_percent_of_amount_as_coin(percent: float, amount: Optional[Coin]) -> Coin:
        """Calculate percentage of amount as Coin value."""
        amount_value = amount.value if amount else 0
        return Coin.value_of(round(percent * amount_value))

    @staticmethod
    def get_maker_fee(is_currency_for_maker_fee_btc: bool, amount: Optional[Coin]) -> Optional[Coin]:
        """
        Calculate maker fee for given amount.
        
        Args:
            is_currency_for_maker_fee_btc: True for BTC fee, False for BSQ fee
            amount: Trading amount in BTC
        """
        if amount is None:
            return None
        fee_per_btc = CoinUtil.get_fee_per_btc(
            FeeService.get_maker_fee_per_btc(is_currency_for_maker_fee_btc), 
            amount
        )
        min_maker_fee = FeeService.get_min_maker_fee(is_currency_for_maker_fee_btc)
        return CoinUtil.max_coin(fee_per_btc, min_maker_fee)

    @staticmethod
    def get_taker_fee(is_currency_for_taker_fee_btc: bool, amount: Optional[Coin]) -> Optional[Coin]:
        """Calculate taker fee for given amount."""
        if amount is None:
            return None
        fee_per_btc = CoinUtil.get_fee_per_btc(
            FeeService.get_taker_fee_per_btc(is_currency_for_taker_fee_btc),
            amount
        )
        min_taker_fee = FeeService.get_min_taker_fee(is_currency_for_taker_fee_btc)
        return CoinUtil.max_coin(fee_per_btc, min_taker_fee)

    @staticmethod
    def get_rounded_fiat_amount(amount: Coin, price: Price, max_trade_limit: int) -> Coin:
        """Get rounded fiat amount considering price and trade limits."""
        return CoinUtil.get_adjusted_amount(amount, price, max_trade_limit, 1)

    @staticmethod
    def get_adjusted_amount_for_hal_cash(amount: Coin, price: Price, max_trade_limit: int) -> Coin:
        """Get adjusted amount for HalCash with factor 10."""
        return CoinUtil.get_adjusted_amount(amount, price, max_trade_limit, 10)

    @staticmethod
    def get_adjusted_amount(amount: Coin, price: Price, max_trade_limit: int, factor: int) -> Coin:
        """
        Calculate adjusted amount considering various constraints.
        
        Args:
            amount: BTC amount to adjust
            price: Current price
            max_trade_limit: Maximum trade limit in satoshis
            factor: Rounding factor for fiat currency
            
        Raises:
            ValueError: If amount < 10k sats or factor <= 0
        """
        check_argument(amount.value >= 10_000, "amount needs to be above minimum of 10k satoshis")
        check_argument(factor > 0, "factor needs to be positive")

        # Amount must result in a volume of min factor units of the fiat currency, e.g. 1 EUR or
        # 10 EUR in case of HalCash.
        smallest_unit_for_volume = Volume.parse(str(factor), price.get_currency_code())
        if smallest_unit_for_volume.value <= 0:
            return Coin.ZERO()

        smallest_unit_for_amount = price.get_amount_by_volume(smallest_unit_for_volume)
        min_trade_amount = Restrictions.get_min_trade_amount().value

        # We use 10 000 satoshi as min allowed amount
        check_argument(min_trade_amount >= 10_000, "MinTradeAmount must be at least 10k satoshis")

        smallest_unit_for_amount = Coin.value_of(max(min_trade_amount, 
                                                   smallest_unit_for_amount.value))
        # We don't allow smaller amount values than smallestUnitForAmount
        use_smallest_unit_for_amount = amount < smallest_unit_for_amount

        # We get the adjusted volume from our amount
        volume = (VolumeUtil.get_adjusted_fiat_volume(
                    price.get_volume_by_amount(smallest_unit_for_amount), factor)
                if use_smallest_unit_for_amount
                else VolumeUtil.get_adjusted_fiat_volume(
                    price.get_volume_by_amount(amount), factor))
    
        if volume.value <= 0:
            return Coin.ZERO()

        # From that adjusted volume we calculate back the amount. It might be a bit different as
        # the amount used as input before due rounding.
        amount_by_volume = price.get_amount_by_volume(volume)
        
        # For the amount we allow only 4 decimal places
        adjusted_amount = round(amount_by_volume.value / 10000) * 10000

        # If we are above our trade limit we reduce the amount by the smallestUnitForAmount
        while adjusted_amount > max_trade_limit:
            adjusted_amount -= smallest_unit_for_amount.value

        adjusted_amount = max(min_trade_amount, adjusted_amount)
        adjusted_amount = min(max_trade_limit, adjusted_amount)
        return Coin.value_of(adjusted_amount)
