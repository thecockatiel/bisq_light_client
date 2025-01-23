from enum import IntEnum


class TransactionConfidenceSource(IntEnum):
    """
    Information about where the transaction was first seen (network, sent direct from peer, created by ourselves).
    Useful for risk analyzing pending transactions. Probably not that useful after a tx is included in the chain,
    unless re-org double spends start happening frequently.
    """

    UNKNOWN = 0
    """We don't know where the transaction came from."""

    NETWORK = 1
    """ We got this transaction from a network peer."""

    SELF = 2
    """This transaction was created by our own wallet, so we know it's not a double spend."""
