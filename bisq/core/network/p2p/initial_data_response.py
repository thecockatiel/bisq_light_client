from abc import ABC, abstractmethod
from typing import Type
from .initial_data_request import InitialDataRequest

class InitialDataResponse(ABC):
    @abstractmethod
    def associated_request(self) -> Type[InitialDataRequest]:
        pass