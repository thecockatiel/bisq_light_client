
from typing import Optional, cast
from bisq.core.locale.country import Country
from bisq.core.locale.country_util import find_country_by_code
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.money_gram_account_payload import MoneyGramAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


class MoneyGramAccount(PaymentAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
        FiatCurrency("AED"),
        FiatCurrency("ARS"),
        FiatCurrency("AUD"),
        FiatCurrency("BND"),
        FiatCurrency("CAD"),
        FiatCurrency("CHF"),
        FiatCurrency("CZK"),
        FiatCurrency("DKK"),
        FiatCurrency("EUR"),
        FiatCurrency("FJD"),
        FiatCurrency("GBP"),
        FiatCurrency("HKD"),
        FiatCurrency("HUF"),
        FiatCurrency("IDR"),
        FiatCurrency("ILS"),
        FiatCurrency("INR"),
        FiatCurrency("JPY"),
        FiatCurrency("KRW"),
        FiatCurrency("KWD"),
        FiatCurrency("LKR"),
        FiatCurrency("MAD"),
        FiatCurrency("MGA"),
        FiatCurrency("MXN"),
        FiatCurrency("MYR"),
        FiatCurrency("NOK"),
        FiatCurrency("NZD"),
        FiatCurrency("OMR"),
        FiatCurrency("PEN"),
        FiatCurrency("PGK"),
        FiatCurrency("PHP"),
        FiatCurrency("PKR"),
        FiatCurrency("PLN"),
        FiatCurrency("SAR"),
        FiatCurrency("SBD"),
        FiatCurrency("SCR"),
        FiatCurrency("SEK"),
        FiatCurrency("SGD"),
        FiatCurrency("THB"),
        FiatCurrency("TOP"),
        FiatCurrency("TRY"),
        FiatCurrency("TWD"),
        FiatCurrency("USD"),
        FiatCurrency("VND"),
        FiatCurrency("VUV"),
        FiatCurrency("WST"),
        FiatCurrency("XOF"),
        FiatCurrency("XPF"),
        FiatCurrency("ZAR")
    ]

    def __init__(self):
        super().__init__(PaymentMethod.MONEY_GRAM)
        self.trade_currencies.extend(MoneyGramAccount.SUPPORTED_CURRENCIES)
        self._country: Optional[Country] = None

    def create_payload(self):
        return MoneyGramAccountPayload(self.payment_method.id, self.id)
    
    def get_supported_currencies(self):
        return MoneyGramAccount.SUPPORTED_CURRENCIES
    
    @property
    def country(self) -> Optional[Country]:
        """country getter. potentially expensive operation as it might need to fetch the country from the code"""
        if self._country is None:
            country_code = self._money_gram_account_payload.country_code
            country = find_country_by_code(country_code)
            if country:
                self._country = country
        return self._country
    
    @country.setter
    def country(self, country: Country) -> None:
        self._country = country
        self._money_gram_account_payload.country_code = country.code

    @property
    def email(self) -> str:
        return self._money_gram_account_payload.email

    @email.setter
    def email(self, email: str) -> None:
        self._money_gram_account_payload.email = email

    @property
    def full_name(self) -> str:
        return self._money_gram_account_payload.holder_name

    @full_name.setter
    def full_name(self, full_name: str) -> None:
        self._money_gram_account_payload.holder_name = full_name

    @property
    def state(self) -> str:
        return self._money_gram_account_payload.state

    @state.setter
    def state(self, state: str) -> None:
        self._money_gram_account_payload.state = state
    
    @property
    def _money_gram_account_payload(self) -> MoneyGramAccountPayload:
        if not isinstance(self.payment_account_payload, MoneyGramAccountPayload):
            raise TypeError(f"Expected MoneyGramAccountPayload, got {type(self.payment_account_payload)}")
        return cast(MoneyGramAccountPayload, self.payment_account_payload)