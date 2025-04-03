from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.clear_xchange_account_payload import (
    ClearXchangeAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


class ClearXchangeAccount(PaymentAccount):

    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
        FiatCurrency("USD"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.CLEAR_X_CHANGE)
        self.set_single_trade_currency(ClearXchangeAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self) -> PaymentAccountPayload:
        return ClearXchangeAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return ClearXchangeAccount.SUPPORTED_CURRENCIES

    @property
    def email_or_mobile_nr(self):
        return self._clear_xchange_account_payload.email_or_mobile_nr

    @email_or_mobile_nr.setter
    def email_or_mobile_nr(self, value: str):
        if value is None:
            value = ""
        self._clear_xchange_account_payload.email_or_mobile_nr = value

    @property
    def holder_name(self):
        return self._clear_xchange_account_payload.holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        if value is None:
            value = ""
        self._clear_xchange_account_payload.holder_name = value

    @property
    def _clear_xchange_account_payload(self):
        assert isinstance(self.payment_account_payload, ClearXchangeAccountPayload)
        return self.payment_account_payload
