from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.tikkie_account_payload import TikkieAccountPayload
from bisq.core.payment.payment_account import CountryBasedPaymentAccount


class TikkieAccount(CountryBasedPaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("EUR")]

    def __init__(self):
        super().__init__(PaymentMethod.TIKKIE)
        self.set_single_trade_currency(TikkieAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self):
        return TikkieAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return TikkieAccount.SUPPORTED_CURRENCIES

    @property
    def iban(self):
        return cast(TikkieAccountPayload, self.payment_account_payload).iban

    @iban.setter
    def iban(self, value: str):
        cast(TikkieAccountPayload, self.payment_account_payload).iban = value or ""

    def get_message_for_buyer(self):
        return "payment.tikkie.info.buyer"

    def get_message_for_seller(self):
        return "payment.tikkie.info.seller"

    def get_message_for_account_creation(self):
        return "payment.tikkie.info.account"
