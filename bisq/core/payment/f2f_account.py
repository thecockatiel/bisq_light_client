from typing import TYPE_CHECKING
from bisq.core.locale.currency_util import get_all_fiat_currencies
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.f2f_account_payload import F2FAccountPayload

if TYPE_CHECKING:
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
    from bisq.core.locale.trade_currency import TradeCurrency


class F2FAccount(CountryBasedPaymentAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = get_all_fiat_currencies()

    def __init__(self):
        super().__init__(PaymentMethod.F2F)

    def create_payload(self) -> "PaymentAccountPayload":
        return F2FAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list["TradeCurrency"]:
        return F2FAccount.SUPPORTED_CURRENCIES

    @property
    def contact(self) -> str:
        return self._f2f_account_payload.contact

    @contact.setter
    def contact(self, contact: str) -> None:
        self._f2f_account_payload.contact = contact

    @property
    def city(self) -> str:
        return self._f2f_account_payload.city

    @city.setter
    def city(self, city: str) -> None:
        self._f2f_account_payload.city = city

    @property
    def extra_info(self) -> str:
        return self._f2f_account_payload.extra_info

    @extra_info.setter
    def extra_info(self, extra_info: str) -> None:
        self._f2f_account_payload.extra_info = extra_info

    @property
    def _f2f_account_payload(self):
        assert isinstance(self.payment_account_payload, F2FAccountPayload)
        return self.payment_account_payload
