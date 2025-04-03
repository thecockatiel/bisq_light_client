from typing import TYPE_CHECKING
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.strike_account_payload import StrikeAccountPayload

if TYPE_CHECKING:
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
    from bisq.core.locale.trade_currency import TradeCurrency


class StrikeAccount(CountryBasedPaymentAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [FiatCurrency("USD")]

    def __init__(self):
        super().__init__(PaymentMethod.STRIKE)
        # this payment method is currently restricted to United States/USD
        self.set_single_trade_currency(StrikeAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self) -> "PaymentAccountPayload":
        return StrikeAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list["TradeCurrency"]:
        return StrikeAccount.SUPPORTED_CURRENCIES

    @property
    def holder_name(self) -> str:
        return self._strike_account_payload.holder_name

    @holder_name.setter
    def holder_name(self, value: str) -> None:
        self._strike_account_payload.holder_name = value

    def get_message_for_buyer(self) -> str:
        return "payment.strike.info.buyer"

    def get_message_for_seller(self) -> str:
        return "payment.strike.info.seller"

    def get_message_for_account_creation(self) -> str:
        return "payment.strike.info.account"

    @property
    def _strike_account_payload(self):
        assert isinstance(self.payment_account_payload, StrikeAccountPayload)
        return self.payment_account_payload
