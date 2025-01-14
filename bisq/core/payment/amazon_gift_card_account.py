from typing import Optional, cast
from bisq.core.locale.country import Country
from bisq.core.locale.country_util import find_country_by_code
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.amazon_gift_card_account_payload import (
    AmazonGiftCardAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.sepa_account_payload import SepaAccountPayload
from bisq.core.payment.payment_account import PaymentAccount


class AmazonGiftCardAccount(PaymentAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
        FiatCurrency("AUD"),
        FiatCurrency("CAD"),
        FiatCurrency("EUR"),
        FiatCurrency("GBP"),
        FiatCurrency("INR"),
        FiatCurrency("JPY"),
        FiatCurrency("SAR"),
        FiatCurrency("SEK"),
        FiatCurrency("SGD"),
        FiatCurrency("TRY"),
        FiatCurrency("USD"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.AMAZON_GIFT_CARD)
        self._country: Optional[Country] = None

    def create_payload(self) -> PaymentAccountPayload:
        return AmazonGiftCardAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return AmazonGiftCardAccount.SUPPORTED_CURRENCIES

    @property
    def email_or_mobile_nr(self):
        return self._amazon_gift_card_account_payload.email_or_mobile_nr

    @email_or_mobile_nr.setter
    def email_or_mobile_nr(self, email_or_mobile_nr: str):
        self._amazon_gift_card_account_payload.email_or_mobile_nr = (
            email_or_mobile_nr
        )

    @property
    def country_not_set(self):
        return self._amazon_gift_card_account_payload.country_not_set

    @property
    def country(self):
        if self._country is None:
            country_code = self._amazon_gift_card_account_payload.country_code
            code = find_country_by_code(country_code)
            if code:
                self._country = code
        return self._country

    @country.setter
    def country(self, country: Country):
        self._country = country
        self._amazon_gift_card_account_payload.country_code = country.code
    
    @property
    def _amazon_gift_card_account_payload(self):
        return cast(AmazonGiftCardAccountPayload, self.payment_account_payload)
