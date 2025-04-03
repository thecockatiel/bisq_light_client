from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.venmo_account_payload import (
    VenmoAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


# Removed due too high chargeback risk
# Cannot be deleted as it would break old trade history entries
class VenmoAccount(PaymentAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [FiatCurrency("USD")]

    def __init__(self):
        super().__init__(PaymentMethod.VENMO)
        self.set_single_trade_currency(VenmoAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self) -> PaymentAccountPayload:
        return VenmoAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return VenmoAccount.SUPPORTED_CURRENCIES

    @property
    def venmo_user_name(self):
        return self._venmo_account_payload.venmo_user_name

    @venmo_user_name.setter
    def venmo_user_name(self, value: str):
        self._venmo_account_payload.venmo_user_name = value

    @property
    def holder_name(self):
        return self._venmo_account_payload.holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        self._venmo_account_payload.holder_name = value

    @property
    def _venmo_account_payload(self):
        assert isinstance(self.payment_account_payload, VenmoAccountPayload)
        return self.payment_account_payload
