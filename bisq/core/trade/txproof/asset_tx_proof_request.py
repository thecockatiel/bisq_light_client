from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Callable

from bisq.common.handlers.fault_handler import FaultHandler


class AssetTxProofRequestResult(ABC):
    pass


_R = TypeVar("_R", bound=AssetTxProofRequestResult)


class AssetTxProofRequest(Generic[_R]):
    @abstractmethod
    def request_from_service(
        self,
        result_handler: Callable[[_R], None],
        fault_handler: FaultHandler,
    ) -> None:
        pass

    @abstractmethod
    def terminate(self) -> None:
        pass
