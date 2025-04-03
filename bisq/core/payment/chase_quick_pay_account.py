from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.chase_quick_pay_account_payload import (
    ChaseQuickPayAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount

# Removed due to QuickPay becoming Zelle
# Cannot be deleted as it would break old trade history entries
# Deprecated
class ChaseQuickPayAccount(PaymentAccount):

    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
        FiatCurrency("USD"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.CHASE_QUICK_PAY)
        self.set_single_trade_currency(ChaseQuickPayAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self) -> PaymentAccountPayload:
        return ChaseQuickPayAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return ChaseQuickPayAccount.SUPPORTED_CURRENCIES

    @property
    def email(self):
        return self._chase_quick_pay_account_payload.email

    @email.setter
    def email(self, value: str):
        if value is None:
            value = ""
        self._chase_quick_pay_account_payload.email = value

    @property
    def holder_name(self):
        return self._chase_quick_pay_account_payload.holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        if value is None:
            value = ""
        self._chase_quick_pay_account_payload.holder_name = value

    @property
    def _chase_quick_pay_account_payload(self):
        assert isinstance(self.payment_account_payload, ChaseQuickPayAccountPayload)
        return self.payment_account_payload
