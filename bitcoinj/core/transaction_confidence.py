from concurrent.futures import Future
from typing import TYPE_CHECKING
from bitcoinj.core.transaction_confidence_source import TransactionConfidenceSource
from bitcoinj.core.transaction_confidence_type import TransactionConfidenceType
from utils.concurrency import ThreadSafeSet

if TYPE_CHECKING:
    from bitcoinj.core.listeners.transaction_confidence_change_reason import (
        TransactionConfidenceChangeReason,
    )
    from bitcoinj.core.listeners.transaction_confidence_changed_listener import (
        TransactionConfidenceChangedListener,
    )


# TODO
class TransactionConfidence:

    def __init__(self) -> None:
        self.depth = -1
        self.hash: bytes = bytes()
        """
        the depth of the transaction in the best chain in blocks. An unconfirmed block has depth 0.
        
        Depth in the chain is an approximation of how much time has elapsed since the transaction has been confirmed.
        On average there is supposed to be a new block every 10 minutes, but the actual rate may vary. Bitcoin Core
        considers a transaction impractical to reverse after 6 blocks, but as of EOY 2011 network
        security is high enough that often only one block is considered enough even for high value transactions. For low
        value transactions like songs, or other cheap items, no blocks at all may be necessary.
        
        If the transaction appears in the top block, the depth is one. If it's anything else (pending, dead, unknown)
        the depth is zero.
        """
        self.confidence_type: "TransactionConfidenceType" = (
            TransactionConfidenceType.UNKNOWN
        )
        self.confidence_source: "TransactionConfidenceSource" = TransactionConfidenceSource.UNKNOWN
        """a general statement of the level of confidence you can have in this transaction."""

        self._listeners = ThreadSafeSet["TransactionConfidenceChangedListener"]()

    def add_listener(self, listener: "TransactionConfidenceChangedListener") -> None:
        self._listeners.add(listener)

    def remove_listener(self, listener: "TransactionConfidenceChangedListener") -> None:
        self._listeners.discard(listener)

    def get_depth_future(self, depth: int) -> Future["TransactionConfidence"]:
        result = Future()

        if self.depth >= depth:
            result.set_result(self)
        else:

            def on_change(
                confidence: "TransactionConfidence",
                reason: "TransactionConfidenceChangeReason",
            ):
                if confidence.depth >= depth:
                    self.remove_listener(on_change)
                    result.set_result(confidence)

            self.add_listener(on_change)

        return result

    def get_depth_in_blocks(self):
        return self.depth
    
    def get_appeared_at_chain_height(self) -> int:
        raise RuntimeError("TransactionConfidence.get_appeared_at_chain_height Not implemented yet")

    def get_transaction_hash(self) -> bytes:
        raise RuntimeError("TransactionConfidence.get_transaction_hash Not implemented yet")
