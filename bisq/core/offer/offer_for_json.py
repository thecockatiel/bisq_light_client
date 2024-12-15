from typing import TYPE_CHECKING, Optional
from datetime import datetime
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.math_utils import MathUtils
from bisq.core.locale.currency_util import is_crypto_currency
from bisq.core.locale.res import Res
from bisq.core.monetary.price import Price
from bisq.core.monetary.volume import Volume
from bisq.core.offer.offer_direction import OfferDirection
from bitcoinj.base.coin import Coin
from bitcoinj.base.utils.monetary_format import MonetaryFormat

if TYPE_CHECKING:
    from bisq.core.payment.payload.payment_method import PaymentMethod

logger = get_logger(__name__)

class OfferForJson:
    FIAT_FORMAT = MonetaryFormat().with_shift(0).with_min_decimals(4).repeat_optional_decimals(0, 0)
    ALTCOIN_FORMAT = MonetaryFormat().with_shift(0).with_min_decimals(8).repeat_optional_decimals(0, 0)
    COIN_FORMAT = MonetaryFormat.BTC()
    
    def __init__(
        self,
        direction: OfferDirection,
        currency_code: str,
        min_amount: Coin,
        amount: Coin,
        price: Optional[Price],
        date: datetime,
        id: str,
        use_market_based_price: bool,
        market_price_margin: float,
        payment_method: 'PaymentMethod'
    ):
        self.direction = direction
        self.currency_code = currency_code
        self.min_amount = min_amount.value
        self.amount = amount.value
        self.price = price.value if price else 0
        self.date = int(date.timestamp() * 1000)
        self.use_market_based_price = use_market_based_price
        self.market_price_margin = market_price_margin
        self.payment_method = payment_method.id
        self.id = id

        # primaryMarket fields are based on industry standard where primaryMarket is always in the focus (in the app BTC is always in the focus - will be changed in a larger refactoring once)
        self.currency_pair: Optional[str] = None
        self.primary_market_direction: OfferDirection = None

        self.price_display_string: Optional[str] = None
        self.primary_market_amount_display_string: Optional[str] = None
        self.primary_market_min_amount_display_string: Optional[str] = None
        self.primary_market_volume_display_string: Optional[str] = None
        self.primary_market_min_volume_display_string: Optional[str] = None

        self.primary_market_price: int = 0
        self.primary_market_amount: int = 0
        self.primary_market_min_amount: int = 0
        self.primary_market_volume: int = 0
        self.primary_market_min_volume: int = 0

        self._set_display_strings()

    def _set_display_strings(self):
        try:
            price = self._get_price()
            if is_crypto_currency(self.currency_code):
                self.primary_market_direction = (OfferDirection.SELL 
                    if self.direction == OfferDirection.BUY else OfferDirection.BUY)
                self.currency_pair = f"{self.currency_code}/{Res.base_currency_code}"

                # amount and volume is inverted for json
                self.price_display_string = OfferForJson.ALTCOIN_FORMAT.no_code().format(price.monetary)
                self.primary_market_min_amount_display_string = OfferForJson.ALTCOIN_FORMAT.no_code().format(self._get_min_volume().monetary)
                self.primary_market_amount_display_string = OfferForJson.ALTCOIN_FORMAT.no_code().format(self._get_volume().monetary)
                self.primary_market_min_volume_display_string = OfferForJson.COIN_FORMAT.no_code().format(self._get_min_amount_as_coin())
                self.primary_market_volume_display_string = OfferForJson.COIN_FORMAT.no_code().format(self._get_amount_as_coin())

                self.primary_market_price = price.value
                self.primary_market_min_amount = self._get_min_volume().value
                self.primary_market_amount = self._get_volume().value
                self.primary_market_min_volume = self._get_min_amount_as_coin().value
                self.primary_market_volume = self._get_amount_as_coin().value
            else:
                self.primary_market_direction = self.direction
                self.currency_pair = f"{Res.base_currency_code}/{self.currency_code}"

                self.price_display_string = OfferForJson.FIAT_FORMAT.no_code().format(price.monetary)
                self.primary_market_min_amount_display_string = OfferForJson.COIN_FORMAT.no_code().format(self._get_min_amount_as_coin())
                self.primary_market_amount_display_string = OfferForJson.COIN_FORMAT.no_code().format(self._get_amount_as_coin())
                self.primary_market_min_volume_display_string = OfferForJson.FIAT_FORMAT.no_code().format(self._get_min_volume().monetary)
                self.primary_market_volume_display_string = OfferForJson.FIAT_FORMAT.no_code().format(self._get_volume().monetary)

                # we use precision 4 for fiat based price but on the markets api we use precision 8
                self.primary_market_price = int(MathUtils.scale_up_by_power_of_10(price.value, 4))
                self.primary_market_min_volume = int(MathUtils.scale_up_by_power_of_10(self._get_min_volume().value, 4))
                self.primary_market_volume = int(MathUtils.scale_up_by_power_of_10(self._get_volume().value, 4))

                self.primary_market_min_amount = self._get_min_amount_as_coin().value
                self.primary_market_amount = self._get_amount_as_coin().value

        except Exception as e:
            logger.error(f"Error at set_display_strings: {str(e)}")

    def _get_price(self) -> Price:
        return Price.value_of(self.currency_code, self.price)

    def _get_amount_as_coin(self) -> Coin:
        return Coin.value_of(self.amount)

    def _get_min_amount_as_coin(self) -> Coin:
        return Coin.value_of(self.min_amount)

    def _get_volume(self) -> Volume:
        return self._get_price().get_volume_by_amount(self._get_amount_as_coin())

    def _get_min_volume(self) -> Volume:
        return self._get_price().get_volume_by_amount(self._get_min_amount_as_coin())
