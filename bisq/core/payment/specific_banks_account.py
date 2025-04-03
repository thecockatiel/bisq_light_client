from typing import TYPE_CHECKING, cast
from bisq.core.locale.currency_util import get_all_fiat_currencies
from bisq.core.payment.bank_name_restricted_bank_account import BankNameRestrictedBankAccount
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.specfic_banks_account_payload import SpecificBanksAccountPayload
from bisq.core.payment.same_country_restricted_bank_account import SameCountryRestrictedBankAccount

if TYPE_CHECKING:
    from bisq.core.locale.trade_currency import TradeCurrency

class SpecificBanksAccount(CountryBasedPaymentAccount, BankNameRestrictedBankAccount, SameCountryRestrictedBankAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = get_all_fiat_currencies()
    
    def __init__(self):
        super().__init__(PaymentMethod.SPECIFIC_BANKS)
        
    def create_payload(self):
        return SpecificBanksAccountPayload(self.payment_method.id, self.id)
    
    def get_supported_currencies(self):
        return SpecificBanksAccount.SUPPORTED_CURRENCIES
    
    @property
    def accepted_banks(self):
        return self._specific_banks_account_payload.accepted_banks
    
    @property
    def bank_id(self):
        return self._specific_banks_account_payload.bank_id
    
    @property
    def country_code(self):
        return self.country.code if self.country else ""
    
    @property
    def _specific_banks_account_payload(self):
        assert isinstance(self.payment_account_payload, SpecificBanksAccountPayload)
        return self.payment_account_payload
