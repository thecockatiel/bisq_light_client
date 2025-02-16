from abc import ABC, abstractmethod


class StateNetworkServiceResponseListener(ABC):
    @abstractmethod
    def on_success(self, serialized_size: int) -> None:
        pass

    @abstractmethod
    def on_fault(self) -> None:
        pass
