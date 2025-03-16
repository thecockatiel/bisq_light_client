from typing import Optional
from bitcoinj.core.transaction_confidence_source import TransactionConfidenceSource
from bitcoinj.core.transaction_confidence_type import TransactionConfidenceType


# TODO
class TransactionConfidence:

    def __init__(
        self,
        tx_id: str,
        *,
        confirmations: Optional[int] = None,
        depth=0,
        appeared_at_chain_height=-1,
        confidence_type: "TransactionConfidenceType" = None,
    ) -> None:
        self.depth = depth
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

        self.tx_id = tx_id
        """The txid that this confidence object is associated with."""

        self.appeared_at_chain_height = appeared_at_chain_height

        if confidence_type is None:
            confidence_type = TransactionConfidenceType.UNKNOWN
        self.confidence_type = confidence_type
        """a general statement of the level of confidence you can have in this transaction."""
        self.confidence_source = TransactionConfidenceSource.NETWORK
        """always Network since we use electrum"""

        self.confirmations = confirmations
        """None if not confirmed"""
