
from abc import ABC, abstractmethod


class BankAccount(ABC):
    
    @property
    @abstractmethod
    def bank_id(self):
        """can only get the bank id, not set it"""
        pass