from bisq.common.setup.log_setup import get_logger
from bisq.common.util.math_utils import MathUtils
from bisq.core.locale.currency_util import is_crypto_currency
from bisq.core.locale.res import Res
from bisq.core.monetary.price import Price
from bisq.core.monetary.volume import Volume
from bitcoinj.base.coin import Coin
from bisq.core.trade.statistics.trade_statistics_3 import TradeStatistics3

logger = get_logger(__name__)


class TradeStatisticsForJson:
    def __init__(self, trade_statistics: "TradeStatistics3"):
        self.currency = trade_statistics.currency
        self.payment_method = trade_statistics.get_payment_method_id()
        self.trade_price = trade_statistics.price
        self.trade_amount = trade_statistics.amount
        self.trade_date = trade_statistics.date

        try:
            trade_price = self.get_trade_price()
            trade_volume = self.get_trade_volume()
            if is_crypto_currency(self.currency):
                self.currency_pair = f"{self.currency}/{Res.base_currency_code}"
                self.primary_market_trade_price = trade_price.get_value()
                self.primary_market_trade_amount = (
                    trade_volume.value if trade_volume is not None else 0
                )
                self.primary_market_trade_volume = self.get_trade_amount().value
            else:
                self.currency_pair = f"{Res.base_currency_code}/{self.currency}"
                # we use precision 4 for fiat based price but on the markets api we use precision 8 so we scale up by 10000
                self.primary_market_trade_price = MathUtils.scale_up_by_power_of_10(
                    trade_price.get_value(), 4
                )
                self.primary_market_trade_amount = self.get_trade_amount().value
                # we use precision 4 for fiat but on the markets api we use precision 8 so we scale up by 10000
                self.primary_market_trade_volume = (
                    MathUtils.scale_up_by_power_of_10(trade_volume.value, 4)
                    if trade_volume is not None
                    else 0
                )
        except Exception as e:
            logger.error(e, exc_info=e)

    def get_trade_price(self):
        return Price.value_of(self.currency, self.trade_price)

    def get_trade_amount(self):
        return Coin.value_of(self.trade_amount)

    def get_trade_volume(self):
        try:
            return self.get_trade_price().get_volume_by_amount(self.get_trade_amount())
        except Exception:
            return Volume.parse("0", self.currency)
