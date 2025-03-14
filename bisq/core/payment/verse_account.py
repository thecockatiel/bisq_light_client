from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.verse_account_payload import VerseAccountPayload
from bisq.core.payment.payment_account import PaymentAccount


class VerseAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [
        FiatCurrency("DKK"),
        FiatCurrency("EUR"),
        FiatCurrency("HUF"),
        FiatCurrency("PLN"),
        FiatCurrency("SEK"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.VERSE)

    def create_payload(self):
        return VerseAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return VerseAccount.SUPPORTED_CURRENCIES

    @property
    def holder_name(self):
        return cast(VerseAccountPayload, self.payment_account_payload).holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        cast(VerseAccountPayload, self.payment_account_payload).holder_name = value or ""

    def get_message_for_buyer(self):
        return "payment.verse.info.buyer"

    def get_message_for_seller(self):
        return "payment.verse.info.seller"

    def get_message_for_account_creation(self):
        return "payment.verse.info.account"