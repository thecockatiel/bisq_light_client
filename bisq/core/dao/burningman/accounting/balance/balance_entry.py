from abc import ABC, abstractmethod
from datetime import datetime


class BalanceEntry(ABC):

    @property
    @abstractmethod
    def date(self) -> datetime:
        pass

    @property
    @abstractmethod
    def month(self) -> datetime:
        pass
