from abc import ABC, abstractmethod

class UidMessage(ABC):
    uid: str
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(self, 'uid'):
            raise RuntimeError(f"You need to have 'uid' in {self.__name__}")