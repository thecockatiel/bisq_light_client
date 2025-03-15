from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.popmoney_account_payload import PopmoneyAccountPayload
from bisq.core.payment.payment_account import PaymentAccount


class PopmoneyAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("USD")]

    def __init__(self):
        super().__init__(PaymentMethod.POPMONEY)
        self.trade_currencies.extend(PopmoneyAccount.SUPPORTED_CURRENCIES)

    def create_payload(self):
        return PopmoneyAccountPayload(self.payment_method.id, self.id)

    @property
    def _popmoney_account_payload(self):
        return cast(PopmoneyAccountPayload, self.payment_account_payload)

    @property
    def account_id(self):
        return self._popmoney_account_payload.account_id

    @account_id.setter
    def account_id(self, value: str):
        self._popmoney_account_payload.account_id = value

    @property
    def holder_name(self):
        return self._popmoney_account_payload.holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        self._popmoney_account_payload.holder_name = value

    def get_supported_currencies(self):
        return PopmoneyAccount.SUPPORTED_CURRENCIES
