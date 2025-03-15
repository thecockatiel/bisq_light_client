from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.strike_account_payload import StrikeAccountPayload
from bisq.core.payment.payment_account import CountryBasedPaymentAccount


class StrikeAccount(CountryBasedPaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("USD")]

    def __init__(self):
        super().__init__(PaymentMethod.STRIKE)
        self.set_single_trade_currency(StrikeAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self):
        return StrikeAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return StrikeAccount.SUPPORTED_CURRENCIES

    @property
    def holder_name(self):
        return cast(StrikeAccountPayload, self.payment_account_payload).holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        cast(StrikeAccountPayload, self.payment_account_payload).holder_name = (
            value or ""
        )

    def get_message_for_buyer(self):
        return "payment.strike.info.buyer"

    def get_message_for_seller(self):
        return "payment.strike.info.seller"

    def get_message_for_account_creation(self):
        return "payment.strike.info.account"
