from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.venmo_account_payload import VenmoAccountPayload
from bisq.core.payment.payment_account import PaymentAccount


class VenmoAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("USD")]

    def __init__(self):
        super().__init__(PaymentMethod.VENMO)
        self.set_single_trade_currency(VenmoAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self):
        return VenmoAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return VenmoAccount.SUPPORTED_CURRENCIES

    @property
    def venmo_user_name(self):
        return cast(VenmoAccountPayload, self.payment_account_payload).venmo_user_name

    @venmo_user_name.setter
    def venmo_user_name(self, value: str):
        cast(VenmoAccountPayload, self.payment_account_payload).venmo_user_name = (
            value or ""
        )

    @property
    def holder_name(self):
        return cast(VenmoAccountPayload, self.payment_account_payload).holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        cast(VenmoAccountPayload, self.payment_account_payload).holder_name = (
            value or ""
        )
