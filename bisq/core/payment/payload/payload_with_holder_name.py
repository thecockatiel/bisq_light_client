
from abc import ABC, abstractmethod


class PayloadWithHolderName(ABC):
    
    @property
    @abstractmethod
    def holder_name(self) -> str:
        pass