from abc import abstractmethod
from bisq.core.payment.bank_account import BankAccount


class SameCountryRestrictedBankAccount(BankAccount):
    
    @property
    @abstractmethod
    def country_code(self) -> str:
        pass