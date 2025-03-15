from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.uphold_account_payload import UpholdAccountPayload
from bisq.core.payment.payment_account import PaymentAccount

class UpholdAccount(PaymentAccount):
    
    SUPPORTED_CURRENCIES = [
        FiatCurrency("AED"),
        FiatCurrency("ARS"),
        FiatCurrency("AUD"),
        FiatCurrency("BRL"),
        FiatCurrency("CAD"),
        FiatCurrency("CHF"),
        FiatCurrency("CNY"),
        FiatCurrency("DKK"),
        FiatCurrency("EUR"),
        FiatCurrency("GBP"),
        FiatCurrency("HKD"),
        FiatCurrency("ILS"),
        FiatCurrency("INR"),
        FiatCurrency("JPY"),
        FiatCurrency("KES"),
        FiatCurrency("MXN"),
        FiatCurrency("NOK"),
        FiatCurrency("NZD"),
        FiatCurrency("PHP"),
        FiatCurrency("PLN"),
        FiatCurrency("SEK"),
        FiatCurrency("SGD"),
        FiatCurrency("USD")
    ]
    
    def __init__(self):
        super().__init__(PaymentMethod.UPHOLD)
        self.trade_currencies.extend(UpholdAccount.SUPPORTED_CURRENCIES)
        
    def create_payload(self):
        return UpholdAccountPayload(self.payment_method.id, self.id)
    
    @property
    def _uphold_account_payload(self):
        return cast(UpholdAccountPayload, self._uphold_account_payload)
    
    @property
    def account_id(self):
        return self._uphold_account_payload.account_id
    
    @property
    def account_owner(self):
        return self._uphold_account_payload.account_owner
    
    @account_owner.setter
    def account_owner(self, value: str):
        self._uphold_account_payload.account_owner = value
    
    def get_supported_currencies(self):
        return UpholdAccount.SUPPORTED_CURRENCIES