from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.perfect_money_account_payload import (
    PerfectMoneyAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


class PerfectMoneyAccount(PaymentAccount):

    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
        FiatCurrency("USD"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.PERFECT_MONEY)
        self.set_single_trade_currency(PerfectMoneyAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self) -> PaymentAccountPayload:
        return PerfectMoneyAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return PerfectMoneyAccount.SUPPORTED_CURRENCIES

    @property
    def account_nr(self):
        return self._perfect_money_account_payload.account_nr

    @account_nr.setter
    def account_nr(self, value):
        self._perfect_money_account_payload.account_nr = value

    @property
    def _perfect_money_account_payload(self):
        assert isinstance(self.payment_account_payload, PerfectMoneyAccountPayload)
        return self.payment_account_payload
