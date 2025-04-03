from typing import TYPE_CHECKING
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.tikkie_account_payload import TikkieAccountPayload

if TYPE_CHECKING:
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
    from bisq.core.locale.trade_currency import TradeCurrency


class TikkieAccount(CountryBasedPaymentAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [FiatCurrency("EUR")]

    def __init__(self):
        super().__init__(PaymentMethod.TIKKIE)
        # this payment method is only for Netherlands/EUR
        self.set_single_trade_currency(TikkieAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self) -> "PaymentAccountPayload":
        return TikkieAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list["TradeCurrency"]:
        return TikkieAccount.SUPPORTED_CURRENCIES

    @property
    def iban(self) -> str:
        return self._tikkie_account_payload.iban

    @iban.setter
    def iban(self, value: str) -> None:
        self._tikkie_account_payload.iban = value

    def get_message_for_buyer(self) -> str:
        return "payment.tikkie.info.buyer"

    def get_message_for_seller(self) -> str:
        return "payment.tikkie.info.seller"

    def get_message_for_account_creation(self) -> str:
        return "payment.tikkie.info.account"

    @property
    def _tikkie_account_payload(self):
        assert isinstance(self.payment_account_payload, TikkieAccountPayload)
        return self.payment_account_payload
