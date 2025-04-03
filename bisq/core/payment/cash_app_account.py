from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.cash_app_account_payload import (
    CashAppAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


# Removed due too high chargeback risk
# Cannot be deleted as it would break old trade history entries
class CashAppAccount(PaymentAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [FiatCurrency("USD")]

    def __init__(self):
        super().__init__(PaymentMethod.CASH_APP)
        self.set_single_trade_currency(CashAppAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self) -> PaymentAccountPayload:
        return CashAppAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return CashAppAccount.SUPPORTED_CURRENCIES

    @property
    def cash_tag(self):
        return self._cash_app_account_payload.cash_tag

    @cash_tag.setter
    def cash_tag(self, value: str):
        self._cash_app_account_payload.cash_tag = value

    @property
    def _cash_app_account_payload(self):
        assert isinstance(self.payment_account_payload, CashAppAccountPayload)
        return self.payment_account_payload
