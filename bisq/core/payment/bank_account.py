
from abc import ABC, abstractmethod
from typing import Optional


class BankAccount(ABC):
    
    @property
    @abstractmethod
    def bank_id(self) -> Optional[str]:
        """can only get the bank id, not set it"""
        pass