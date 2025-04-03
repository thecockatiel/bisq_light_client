from typing import TYPE_CHECKING
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.bizum_account_payload import BizumAccountPayload

if TYPE_CHECKING:
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
    from bisq.core.locale.trade_currency import TradeCurrency


class BizumAccount(CountryBasedPaymentAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [FiatCurrency("EUR")]

    def __init__(self):
        super().__init__(PaymentMethod.BIZUM)

    def create_payload(self) -> "PaymentAccountPayload":
        return BizumAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list["TradeCurrency"]:
        return BizumAccount.SUPPORTED_CURRENCIES

    @property
    def mobile_nr(self) -> str:
        return self._bizum_account_payload.mobile_nr

    @mobile_nr.setter
    def mobile_nr(self, value: str) -> None:
        self._bizum_account_payload.mobile_nr = value

    def get_message_for_buyer(self) -> str:
        return "payment.bizum.info.buyer"

    def get_message_for_seller(self) -> str:
        return "payment.bizum.info.seller"

    def get_message_for_account_creation(self) -> str:
        return "payment.bizum.info.account"

    @property
    def _bizum_account_payload(self):
        assert isinstance(self.payment_account_payload, BizumAccountPayload)
        return self.payment_account_payload
