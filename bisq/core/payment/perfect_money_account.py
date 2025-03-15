from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.perfect_money_account_payload import (
    PerfectMoneyAccountPayload,
)
from bisq.core.payment.payment_account import PaymentAccount


class PerfectMoneyAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("USD")]

    def __init__(self):
        super().__init__(PaymentMethod.PERFECT_MONEY)
        self.trade_currencies.extend(PerfectMoneyAccount.SUPPORTED_CURRENCIES)

    def create_payload(self):
        return PerfectMoneyAccountPayload(self.payment_method.id, self.id)

    @property
    def _perfect_money_account_payload(self):
        return cast(PerfectMoneyAccountPayload, self.payment_account_payload)

    @property
    def account_nr(self):
        return self._perfect_money_account_payload.account_nr

    @account_nr.setter
    def account_nr(self, value: str):
        self._perfect_money_account_payload.account_nr = value

    def get_supported_currencies(self):
        return PerfectMoneyAccount.SUPPORTED_CURRENCIES
