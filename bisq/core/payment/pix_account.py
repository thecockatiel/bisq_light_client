from typing import TYPE_CHECKING
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.pix_account_payload import PixAccountPayload

if TYPE_CHECKING:
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
    from bisq.core.locale.trade_currency import TradeCurrency


class PixAccount(CountryBasedPaymentAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [FiatCurrency("BRL")]

    def __init__(self):
        super().__init__(PaymentMethod.PIX)

    def create_payload(self) -> "PaymentAccountPayload":
        return PixAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list["TradeCurrency"]:
        return PixAccount.SUPPORTED_CURRENCIES

    @property
    def pix_key(self) -> str:
        return self._pix_account_payload.pix_key

    @pix_key.setter
    def pix_key(self, value: str) -> None:
        self._pix_account_payload.pix_key = value

    def get_message_for_buyer(self) -> str:
        return "payment.pix.info.buyer"

    def get_message_for_seller(self) -> str:
        return "payment.pix.info.seller"

    def get_message_for_account_creation(self) -> str:
        return "payment.pix.info.account"

    @property
    def _pix_account_payload(self):
        assert isinstance(self.payment_account_payload, PixAccountPayload)
        return self.payment_account_payload
