from abc import ABC, abstractmethod

class UidMessage(ABC):

    @abstractmethod
    def get_uid(self) -> str:
        pass