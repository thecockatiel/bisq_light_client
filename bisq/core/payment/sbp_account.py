from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.sbp_account_payload import (
    SbpAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


class SbpAccount(PaymentAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [FiatCurrency("RUB")]

    def __init__(self):
        super().__init__(PaymentMethod.SBP)
        self.set_single_trade_currency(SbpAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self) -> PaymentAccountPayload:
        return SbpAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return SbpAccount.SUPPORTED_CURRENCIES

    @property
    def mobile_number(self):
        return self._sbp_account_payload.mobile_number

    @mobile_number.setter
    def mobile_number(self, value: str):
        self._sbp_account_payload.mobile_number = value

    @property
    def bank_name(self):
        return self._sbp_account_payload.bank_name

    @bank_name.setter
    def bank_name(self, value: str):
        self._sbp_account_payload.bank_name = value

    def get_message_for_account_creation(self) -> str:
        return "payment.sbp.info.account"

    @property
    def _sbp_account_payload(self):
        assert isinstance(self.payment_account_payload, SbpAccountPayload)
        return self.payment_account_payload
