from abc import ABC, abstractmethod


class DaoSetupService(ABC):
    """
    All main service classes implements that interface to guarantee a controlled
    startup sequence.
    """
    
    @abstractmethod
    def add_listeners(self):
        pass
    
    @abstractmethod
    def start(self):
        pass
