from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.faster_payments_account_payload import (
    FasterPaymentsAccountPayload,
)
from bisq.core.payment.payment_account import PaymentAccount


class FasterPaymentsAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("GBP")]

    def __init__(self):
        super().__init__(PaymentMethod.FASTER_PAYMENTS)
        self.trade_currencies.extend(FasterPaymentsAccount.SUPPORTED_CURRENCIES)

    def create_payload(self):
        return FasterPaymentsAccountPayload(self.payment_method.id, self.id)

    @property
    def _faster_payments_account_payload(self):
        return cast(FasterPaymentsAccountPayload, self.payment_account_payload)

    @property
    def holder_name(self):
        return self._faster_payments_account_payload.holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        self._faster_payments_account_payload.holder_name = value

    @property
    def sort_code(self):
        return self._faster_payments_account_payload.sort_code

    @sort_code.setter
    def sort_code(self, value: str):
        self._faster_payments_account_payload.sort_code = value

    @property
    def account_nr(self):
        return self._faster_payments_account_payload.account_nr

    @account_nr.setter
    def account_nr(self, value: str):
        self._faster_payments_account_payload.account_nr = value

    def get_supported_currencies(self):
        return FasterPaymentsAccount.SUPPORTED_CURRENCIES
