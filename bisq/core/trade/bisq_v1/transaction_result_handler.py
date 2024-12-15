
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction


class TransactionResultHandler(ABC):
    
    @abstractmethod
    def handle_result(self, result: "Transaction"):
        pass
    
    def __call__(self, result: "Transaction"):
        return self.handle_result()