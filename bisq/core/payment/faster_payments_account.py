from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.faster_payments_account_payload import (
    FasterPaymentsAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


class FasterPaymentsAccount(PaymentAccount):

    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
        FiatCurrency("GBP"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.FASTER_PAYMENTS)
        self.set_single_trade_currency(FasterPaymentsAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self) -> PaymentAccountPayload:
        return FasterPaymentsAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return FasterPaymentsAccount.SUPPORTED_CURRENCIES

    @property
    def account_nr(self):
        return self._faster_payments_account_payload.account_nr

    @account_nr.setter
    def account_nr(self, value):
        self._faster_payments_account_payload.account_nr = value

    @property
    def holder_name(self):
        return self._faster_payments_account_payload.holder_name

    @holder_name.setter
    def holder_name(self, value):
        self._faster_payments_account_payload.holder_name = value

    @property
    def sort_code(self):
        return self._faster_payments_account_payload.sort_code

    @sort_code.setter
    def sort_code(self, value):
        self._faster_payments_account_payload.sort_code = value

    @property
    def _faster_payments_account_payload(self):
        assert isinstance(self.payment_account_payload, FasterPaymentsAccountPayload)
        return self.payment_account_payload
