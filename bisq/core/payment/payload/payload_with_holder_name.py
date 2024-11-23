
from abc import ABC, abstractmethod


class PayloadWithHolderName(ABC):
    
    @abstractmethod
    def get_holder_name(self) -> str:
        pass