from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.cash_app_account_payload import CashAppAccountPayload
from bisq.core.payment.payment_account import PaymentAccount


class CashAppAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("USD")]

    def __init__(self):
        super().__init__(PaymentMethod.CASH_APP)
        self.set_single_trade_currency(CashAppAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self):
        return CashAppAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return CashAppAccount.SUPPORTED_CURRENCIES

    @property
    def cash_tag(self):
        return cast(CashAppAccountPayload, self.payment_account_payload).cash_tag

    @cash_tag.setter
    def cash_tag(self, value: str):
        cast(CashAppAccountPayload, self.payment_account_payload).cash_tag = value or ""
