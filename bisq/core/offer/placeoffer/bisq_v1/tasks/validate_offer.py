from typing import TYPE_CHECKING
from bitcoinj.base.coin import Coin
from bisq.common.taskrunner.task import Task
from typing import Optional

from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.offer.placeoffer.bisq_v1.place_offer_model import PlaceOfferModel
    from bisq.common.taskrunner.task_runner import TaskRunner
    from bisq.core.trade.protocol.trade_message import TradeMessage

class ValidateOffer(Task['PlaceOfferModel']):
    def __init__(self, task_handler: 'TaskRunner[PlaceOfferModel]', model: 'PlaceOfferModel'):
        super().__init__(task_handler, model)
        
    def run(self):
        offer = self.model.offer
        try:
            self.run_intercept_hook()

            check_argument(not offer.is_bsq_swap_offer, "BSQ swap offers not supported")

            # Validate coins
            self.check_coin_not_null_or_zero(offer.amount, "Amount")
            self.check_coin_not_null_or_zero(offer.min_amount, "MinAmount")
            self.check_coin_not_null_or_zero(offer.maker_fee, "MakerFee")
            self.check_coin_not_null_or_zero(offer.buyer_security_deposit, "buyerSecurityDeposit")
            self.check_coin_not_null_or_zero(offer.seller_security_deposit, "sellerSecurityDeposit")
            self.check_coin_not_null_or_zero(offer.tx_fee, "txFee")
            self.check_coin_not_null_or_zero(offer.max_trade_limit, "MaxTradeLimit")

            # Amount validations
            check_argument(offer.amount <= offer.payment_method.get_max_trade_limit_as_coin(offer.currency_code),
                           f"Amount is larger than {offer.payment_method.get_max_trade_limit_as_coin(offer.currency_code).to_friendly_string()}")
            check_argument(offer.amount >= offer.min_amount, "MinAmount is larger than Amount")

            # Price validations
            assert offer.get_price() is not None, "Price is null"
            check_argument(offer.get_price().is_positive(), f"Price must be positive. price={offer.get_price().to_friendly_string()}")

            # Date validation
            check_argument(offer.date.timestamp() > 0, f"Date must not be 0. date={offer.date}")

            # Other validations
            assert offer.currency_code is not None, "Currency is null"
            assert offer.direction is not None, "Direction is null"
            assert offer.id is not None, "Id is null"
            assert offer.pub_key_ring is not None, "pubKeyRing is null"
            assert offer.min_amount is not None, "MinAmount is null"
            assert offer.get_price() is not None, "Price is null"
            assert offer.tx_fee is not None, "txFee is null"
            assert offer.maker_fee is not None, "MakerFee is null"
            assert offer.version_nr is not None, "VersionNr is null"
            check_argument(offer.max_trade_period > 0, f"maxTradePeriod must be positive. maxTradePeriod={offer.max_trade_period}")
            # JAVA TODO check upper and lower bounds for fiat
            # JAVA TODO check rest of new parameters
            # JAVA TODO check for account age witness base tradeLimit is missing

            self.complete()
        except Exception as e:
            offer.error_message = f"An error occurred.\nError message:\n{str(e)}"
            self.failed(exc=e)

    @staticmethod
    def check_coin_not_null_or_zero(value: Optional[Coin], name: str) -> None:
        assert value is not None, f"{name} is None"
        check_argument(value.is_positive(), f"{name} must be positive. {name}={value.to_friendly_string()}")

    @staticmethod
    def non_empty_string_of(value: Optional[str]) -> str:
        assert value is not None, "String value is None"
        check_argument(len(value) > 0, "String value is empty")
        return value

    @staticmethod
    def non_negative_long_of(value: int) -> int:
        check_argument(value >= 0, "Value must be non-negative")
        return value

    @staticmethod
    def non_zero_coin_of(value: Optional[Coin]) -> Coin:
        assert value is not None, "Coin value is None"
        check_argument(not value.is_zero(), "Coin value is zero")
        return value

    @staticmethod
    def positive_coin_of(value: Optional[Coin]) -> Coin:
        assert value is not None, "Coin value is None"
        check_argument(value.is_positive(), "Coin value must be positive")
        return value

    @staticmethod
    def check_trade_id(trade_id: str, trade_message: 'TradeMessage') -> None:
        check_argument(trade_id == trade_message.trade_id, "Trade IDs do not match")
