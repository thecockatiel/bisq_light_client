from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from bisq.core.trade.txproof.asset_tx_proof_model import AssetTxProofModel
    from bisq.core.trade.txproof.asset_tx_proof_request import AssetTxProofRequestResult

_R = TypeVar("_R", bound="AssetTxProofRequestResult")
_T = TypeVar("_T", bound="AssetTxProofModel")

class AssetTxProofParser(Generic[_R, _T], ABC):

    @abstractmethod
    def parse(
        self, json_txt: str, model: _T = None
    ) -> _R:
        pass
