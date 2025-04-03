from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.popmoney_account_payload import (
    PopmoneyAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


# JAVA TODO missing support for selected trade currency
class PopmoneyAccount(PaymentAccount):

    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
        FiatCurrency("USD"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.POPMONEY)
        self.set_single_trade_currency(PopmoneyAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self) -> PaymentAccountPayload:
        return PopmoneyAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return PopmoneyAccount.SUPPORTED_CURRENCIES

    @property
    def account_id(self):
        return self._popmoney_account_payload.account_id

    @account_id.setter
    def account_id(self, value):
        self._popmoney_account_payload.account_id = value

    @property
    def holder_name(self):
        return self._popmoney_account_payload.holder_name

    @holder_name.setter
    def holder_name(self, value):
        self._popmoney_account_payload.holder_name = value

    @property
    def _popmoney_account_payload(self):
        assert isinstance(self.payment_account_payload, PopmoneyAccountPayload)
        return self.payment_account_payload
