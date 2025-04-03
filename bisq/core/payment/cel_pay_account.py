from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.cel_pay_account_payload import (
    CelPayAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


class CelPayAccount(PaymentAccount):

    #  https://github.com/bisq-network/growth/issues/231
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
        FiatCurrency("AUD"),
        FiatCurrency("CAD"),
        FiatCurrency("GBP"),
        FiatCurrency("HKD"),
        FiatCurrency("USD"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.CELPAY)

    def create_payload(self) -> PaymentAccountPayload:
        return CelPayAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return CelPayAccount.SUPPORTED_CURRENCIES

    @property
    def email(self):
        return self._cel_pay_account_payload.email

    @email.setter
    def email(self, value: str):
        self._cel_pay_account_payload.email = value

    def get_message_for_buyer(self) -> str:
        return "payment.celpay.info.buyer"

    def get_message_for_seller(self) -> str:
        return "payment.celpay.info.seller"

    def get_message_for_account_creation(self) -> str:
        return "payment.celpay.info.account"

    @property
    def _cel_pay_account_payload(self):
        assert isinstance(self.payment_account_payload, CelPayAccountPayload)
        return self.payment_account_payload
