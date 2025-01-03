from abc import ABC, abstractmethod
from typing import Callable
from bisq.common.handlers.fault_handler import FaultHandler
from bisq.core.trade.txproof.asset_tx_proof_result import AssetTxProofResult


class AssetTxProofRequestsPerTrade(ABC):
    @abstractmethod
    def request_from_all_services(
        self,
        result_handler: Callable[[AssetTxProofResult], None],
        fault_handler: FaultHandler,
    ) -> None:
        pass

    @abstractmethod
    def terminate(self) -> None:
        pass
