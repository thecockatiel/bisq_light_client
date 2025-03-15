from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.money_beam_account_payload import MoneyBeamAccountPayload
from bisq.core.payment.payment_account import PaymentAccount


class MoneyBeamAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("EUR")]

    def __init__(self):
        super().__init__(PaymentMethod.MONEY_BEAM)
        self.trade_currencies.extend(MoneyBeamAccount.SUPPORTED_CURRENCIES)

    def create_payload(self):
        return MoneyBeamAccountPayload(self.payment_method.id, self.id)

    @property
    def _money_beam_account_payload(self):
        return cast(MoneyBeamAccountPayload, self.payment_account_payload)

    @property
    def account_id(self):
        return self._money_beam_account_payload.account_id

    @account_id.setter
    def account_id(self, value: str):
        self._money_beam_account_payload.account_id = value

    def get_supported_currencies(self):
        return MoneyBeamAccount.SUPPORTED_CURRENCIES
