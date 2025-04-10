from typing import TYPE_CHECKING
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.nequi_account_payload import NequiAccountPayload

if TYPE_CHECKING:
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
    from bisq.core.locale.trade_currency import TradeCurrency


class NequiAccount(CountryBasedPaymentAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [FiatCurrency("COP")]

    def __init__(self):
        super().__init__(PaymentMethod.NEQUI)

    def create_payload(self) -> "PaymentAccountPayload":
        return NequiAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list["TradeCurrency"]:
        return NequiAccount.SUPPORTED_CURRENCIES

    @property
    def mobile_nr(self) -> str:
        return self._nequi_account_payload.mobile_nr

    @mobile_nr.setter
    def mobile_nr(self, value: str) -> None:
        self._nequi_account_payload.mobile_nr = value

    def get_message_for_buyer(self) -> str:
        return "payment.nequi.info.buyer"

    def get_message_for_seller(self) -> str:
        return "payment.nequi.info.seller"

    def get_message_for_account_creation(self) -> str:
        return "payment.nequi.info.account"

    @property
    def _nequi_account_payload(self):
        assert isinstance(self.payment_account_payload, NequiAccountPayload)
        return self.payment_account_payload
