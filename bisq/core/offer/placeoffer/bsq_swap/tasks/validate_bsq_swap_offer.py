from typing import TYPE_CHECKING
from bisq.common.taskrunner.task import Task
from bitcoinj.base.coin import Coin
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.offer.placeoffer.bsq_swap.place_bsq_swap_offer_model import (
        PlaceBsqSwapOfferModel,
    )


class ValidateBsqSwapOffer(Task["PlaceBsqSwapOfferModel"]):

    def run(self) -> None:
        offer = self.model.offer
        try:
            self.run_intercept_hook()
            check_argument(offer.is_bsq_swap_offer, "Offer must be BsqSwapOfferPayload")

            # Coins
            self.check_coin_not_none_or_zero(offer.amount, "Amount")
            self.check_coin_not_none_or_zero(offer.min_amount, "MinAmount")

            check_argument(
                offer.amount <= offer.payment_method.get_max_trade_limit_as_coin(offer.currency_code),
                f"Amount is larger than {offer.payment_method.get_max_trade_limit_as_coin(offer.currency_code).to_friendly_string()}"
            )
            check_argument(
                offer.amount >= offer.min_amount,
                "MinAmount is larger than Amount"
            )

            price = offer.get_price()
            if price is None:
                raise ValueError("Price is None")
            check_argument(price.is_positive(), f"Price must be positive. price={price.to_friendly_string()}")
            check_argument(offer.date.timestamp() > 0, f"Date must not be 0. date={offer.date}")

            for attr, name in [
                (offer.currency_code, "Currency"),
                (offer.direction, "Direction"),
                (offer.id, "Id"),
                (offer.pub_key_ring, "pubKeyRing"),
                (offer.min_amount, "MinAmount"),
                (offer.version_nr, "VersionNr"),
            ]:
                if attr is None:
                    raise ValueError(f"{name} is None")

            self.complete()
        except Exception as e:
            offer.error_message = f"An error occurred.\nError message:\n{str(e)}"
            self.failed(exc=e)

    @staticmethod
    def check_coin_not_none_or_zero(value: "Coin", name: str) -> None:
        if value is None:
            raise ValueError(f"{name} is None")
        check_argument(value.is_positive(), f"{name} must be positive. {name}={value.to_friendly_string()}")
