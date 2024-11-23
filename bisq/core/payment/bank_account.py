
from abc import ABC, abstractmethod


class BankAccount(ABC):
    
    @abstractmethod
    def get_bank_id(self):
        pass