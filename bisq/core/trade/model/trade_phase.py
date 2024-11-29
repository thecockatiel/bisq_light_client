from abc import ABC, abstractmethod
from enum import Enum

class TradePhase(ABC):
    @abstractmethod
    def ordinal(self) -> int:
        pass
    
    @abstractmethod
    def name(self) -> str:
        pass
    
    class Phase(Enum):
        DEFAULT = 0
        
        def ordinal(self) -> int:
            return self.value
            
        def name(self) -> str:
            return self._name_
