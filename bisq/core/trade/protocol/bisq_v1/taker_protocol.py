
from abc import ABC, abstractmethod


class TakerProtocol(ABC):
    
    @abstractmethod
    def on_take_offer(self):
        pass
    
    