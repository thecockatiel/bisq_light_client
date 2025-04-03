from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.money_beam_account_payload import (
    MoneyBeamAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


# JAVA TODO missing support for selected trade currency
class MoneyBeamAccount(PaymentAccount):

    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
        FiatCurrency("EUR"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.MONEY_BEAM)
        self.set_single_trade_currency(MoneyBeamAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self) -> PaymentAccountPayload:
        return MoneyBeamAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return MoneyBeamAccount.SUPPORTED_CURRENCIES

    @property
    def account_id(self):
        return self._money_beam_account_payload.account_id

    @account_id.setter
    def account_id(self, value):
        self._money_beam_account_payload.account_id = value

    @property
    def _money_beam_account_payload(self):
        assert isinstance(self.payment_account_payload, MoneyBeamAccountPayload)
        return self.payment_account_payload
