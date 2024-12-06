
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bitcoinj.core.listeners.transaction_confidence_change_reason import TransactionConfidenceChangeReason
    from bitcoinj.core.transaction_confidence import TransactionConfidence


class TransactionConfidenceChangedListener(Callable[["TransactionConfidence", "TransactionConfidenceChangeReason"], None], ABC):
    
    @abstractmethod
    def on_confidence_changed(self, new_confidence: "TransactionConfidence", reason: "TransactionConfidenceChangeReason"):
        pass
    
    def __call__(self, new_confidence: "TransactionConfidence", reason: "TransactionConfidenceChangeReason"):
        self.on_confidence_changed(new_confidence, reason)