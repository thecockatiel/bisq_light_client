from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.verse_account_payload import (
    VerseAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


class VerseAccount(PaymentAccount):

    #  https://github.com/bisq-network/growth/issues/223
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
        FiatCurrency("DKK"),
        FiatCurrency("EUR"),
        FiatCurrency("HUF"),
        FiatCurrency("PLN"),
        FiatCurrency("SEK"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.VERSE)

    def create_payload(self) -> PaymentAccountPayload:
        return VerseAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return VerseAccount.SUPPORTED_CURRENCIES

    @property
    def holder_name(self):
        return self._verse_account_payload.holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        self._verse_account_payload.holder_name = value

    def get_message_for_buyer(self) -> str:
        return "payment.verse.info.buyer"

    def get_message_for_seller(self) -> str:
        return "payment.verse.info.seller"

    def get_message_for_account_creation(self) -> str:
        return "payment.verse.info.account"

    @property
    def _verse_account_payload(self):
        assert isinstance(self.payment_account_payload, VerseAccountPayload)
        return self.payment_account_payload
