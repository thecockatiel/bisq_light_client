from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bitcoinj.core.transaction_confidence import TransactionConfidence


class TxConfidenceListener(ABC):
    def __init__(self, tx_id: str):
        self.tx_id = tx_id

    @abstractmethod
    def on_transaction_confidence_changed(self, confidence: "TransactionConfidence"):
        pass
