
from typing import cast
from bisq.core.locale.country_util import get_all_sepa_countries
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.bank_account import BankAccount
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.sepa_instant_account_payload import SepaInstantAccountPayload


class SepaInstantAccount(CountryBasedPaymentAccount, BankAccount):
        SUPPORTED_CURRENCIES: list["TradeCurrency"] = [FiatCurrency("EUR")]
        
        def __init__(self):
            super().__init__(PaymentMethod.SEPA_INSTANT)
            self.set_single_trade_currency(SepaInstantAccount.SUPPORTED_CURRENCIES[0])
            
        def create_payload(self) -> PaymentAccountPayload:
            return SepaInstantAccountPayload(self.payment_method.id, self.id, accepted_countries=get_all_sepa_countries())
        
        @property
        def bank_id(self):
            return cast(SepaInstantAccountPayload, self.payment_account_payload).bic
        
        @property
        def holder_name(self):
            return self.payment_account_payload.holder_name
        
        @holder_name.setter
        def holder_name(self, holder_name: str):
            self.payment_account_payload.holder_name = holder_name
        
        @property
        def iban(self):
            return cast(SepaInstantAccountPayload, self.payment_account_payload).iban
        
        @iban.setter
        def iban(self, iban: str):
            cast(SepaInstantAccountPayload, self.payment_account_payload).iban = iban
        
        @property
        def bic(self):
            return cast(SepaInstantAccountPayload, self.payment_account_payload).bic
        
        @bic.setter
        def bic(self, bic: str):
            cast(SepaInstantAccountPayload, self.payment_account_payload).bic = bic
        
        @property
        def accepted_country_codes(self):
            return cast(SepaInstantAccountPayload, self.payment_account_payload).accepted_country_codes
        
        def add_accepted_country_code(self, country_code: str):
            cast(SepaInstantAccountPayload, self.payment_account_payload).add_accepted_country(country_code)
        
        def remove_accepted_country_code(self, country_code: str):
            cast(SepaInstantAccountPayload, self.payment_account_payload).remove_accepted_country(country_code)
            
        def on_persist_changes(self):
            super().on_persist_changes()
            cast(SepaInstantAccountPayload, self.payment_account_payload).on_persist_changes()
            
        def on_revert_changes(self):
            super().revert_changes()
            cast(SepaInstantAccountPayload, self.payment_account_payload).revert_changes()
            
        def get_supported_currencies(self) -> list[TradeCurrency]:
            return SepaInstantAccount.SUPPORTED_CURRENCIES