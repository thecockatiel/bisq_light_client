from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.us_postal_money_order_account_payload import (
    USPostalMoneyOrderAccountPayload,
)
from bisq.core.payment.payment_account import PaymentAccount


class USPostalMoneyOrderAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("USD")]

    def __init__(self):
        super().__init__(PaymentMethod.US_POSTAL_MONEY_ORDER)
        self.set_single_trade_currency(
            USPostalMoneyOrderAccount.SUPPORTED_CURRENCIES[0]
        )

    def create_payload(self):
        return USPostalMoneyOrderAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return USPostalMoneyOrderAccount.SUPPORTED_CURRENCIES

    @property
    def postal_address(self):
        return cast(
            USPostalMoneyOrderAccountPayload, self.payment_account_payload
        ).postal_address

    @postal_address.setter
    def postal_address(self, value: str):
        cast(
            USPostalMoneyOrderAccountPayload, self.payment_account_payload
        ).postal_address = (value or "")

    @property
    def holder_name(self):
        return cast(
            USPostalMoneyOrderAccountPayload, self.payment_account_payload
        ).holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        cast(
            USPostalMoneyOrderAccountPayload, self.payment_account_payload
        ).holder_name = (value or "")
