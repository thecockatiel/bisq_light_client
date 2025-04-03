from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.monese_account_payload import (
    MoneseAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


class MoneseAccount(PaymentAccount):

    # https://github.com/bisq-network/growth/issues/227
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
        FiatCurrency("EUR"),
        FiatCurrency("GBP"),
        FiatCurrency("RON"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.MONESE)

    def create_payload(self) -> PaymentAccountPayload:
        return MoneseAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return MoneseAccount.SUPPORTED_CURRENCIES

    @property
    def holder_name(self):
        return self._monese_account_payload.holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        self._monese_account_payload.holder_name = value

    @property
    def mobile_nr(self):
        return self._monese_account_payload.mobile_nr

    @mobile_nr.setter
    def mobile_nr(self, value: str):
        self._monese_account_payload.mobile_nr = value

    def get_message_for_buyer(self) -> str:
        return "payment.monese.info.buyer"

    def get_message_for_seller(self) -> str:
        return "payment.monese.info.seller"

    def get_message_for_account_creation(self) -> str:
        return "payment.monese.info.account"

    @property
    def _monese_account_payload(self):
        assert isinstance(self.payment_account_payload, MoneseAccountPayload)
        return self.payment_account_payload
