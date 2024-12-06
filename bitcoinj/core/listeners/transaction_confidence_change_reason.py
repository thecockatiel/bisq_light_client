from enum import IntEnum


class TransactionConfidenceChangeReason(IntEnum):
    TYPE = 0
    """
    Occurs when the TransactionConfidence.confidence_type has changed.
    For example, if a PENDING transaction changes to BUILDING or DEAD, then this reason will
    be given. It's a high level summary.
    """

    DEPTH = 1
    """
    Occurs when a transaction that is in the best known block chain gets buried by another block. If you're
    waiting for a certain number of confirmations, this is the reason to watch out for.
    """

    SEEN_PEERS = 2
    """
    Occurs when a pending transaction (not in the chain) was announced by another connected peers. By
    watching the number of peers that announced a transaction go up, you can see whether it's being
    accepted by the network or not. If all your peers announce, it's a pretty good bet the transaction
    is considered relayable and has thus reached the miners.
    """
