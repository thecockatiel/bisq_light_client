from typing import TYPE_CHECKING
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.satispay_account_payload import SatispayAccountPayload

if TYPE_CHECKING:
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
    from bisq.core.locale.trade_currency import TradeCurrency


class SatispayAccount(CountryBasedPaymentAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [FiatCurrency("EUR")]

    def __init__(self):
        super().__init__(PaymentMethod.SATISPAY)

    def create_payload(self) -> "PaymentAccountPayload":
        return SatispayAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list["TradeCurrency"]:
        return SatispayAccount.SUPPORTED_CURRENCIES

    @property
    def holder_name(self) -> str:
        return self._satispay_account_payload.holder_name

    @holder_name.setter
    def holder_name(self, value: str) -> None:
        self._satispay_account_payload.holder_name = value

    @property
    def mobile_nr(self) -> str:
        return self._satispay_account_payload.mobile_nr

    @mobile_nr.setter
    def mobile_nr(self, value: str) -> None:
        self._satispay_account_payload.mobile_nr = value

    def get_message_for_buyer(self) -> str:
        return "payment.satispay.info.buyer"

    def get_message_for_seller(self) -> str:
        return "payment.satispay.info.seller"

    def get_message_for_account_creation(self) -> str:
        return "payment.satispay.info.account"

    @property
    def _satispay_account_payload(self):
        assert isinstance(self.payment_account_payload, SatispayAccountPayload)
        return self.payment_account_payload
