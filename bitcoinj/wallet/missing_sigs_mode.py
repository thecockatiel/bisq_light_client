from enum import IntEnum, auto


class MissingSigsMode(IntEnum):
    USE_OP_ZERO = auto()
    """Input script will have OP_0 instead of missing signatures"""

    USE_DUMMY_SIG = auto()
    """
    Missing signatures will be replaced by dummy sigs. 
    This is useful when you'd like to know the fee for a transaction without 
    knowing the user's password, as fee depends on size.
    """

    THROW = auto()
    """
    If signature is missing, TransactionSigner.MissingSignatureException
    will be thrown for P2SH and ECKey.MissingPrivateKeyException for other tx types.
    """