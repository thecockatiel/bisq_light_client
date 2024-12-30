from typing import TYPE_CHECKING, Optional

from bitcoinj.core.sha_256_hash import Sha256Hash

if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.core.transaction_output import TransactionOutput


# TODO
class TransactionOutPoint:
    MESSAGE_LENGTH = 36

    def __init__(self, *, from_tx: Optional["Transaction"] = None, hash: "Sha256Hash" = None, connected_output: "TransactionOutput" = None, index: int = None):
        """only either of from_tx or hash or connected_output should be set"""
        
        if sum(x is not None for x in [from_tx, hash, connected_output]) > 1:
            raise ValueError("Only one of from_tx, hash, or connected_output should be set")
        
        self.index = 0
        self.from_tx: Optional["Transaction"] = None
        self.hash: "Sha256Hash" = None
        self.connected_output: "TransactionOutput" = None
        self.length = TransactionOutPoint.MESSAGE_LENGTH
        
        if connected_output is not None:
            self.index = connected_output.index
            self.hash = connected_output.get_parent_transaction_hash()
            self.connected_output = connected_output
        elif hash is not None:
            if index is None:
                raise ValueError("index must be set when hash is set")
            self.index = index
            self.hash = hash
        else:
            if index is None:
                raise ValueError("index must be set when from_tx is set")
            # from_tx can be none
            if from_tx is not None:
                self.hash = from_tx.get_tx_id()
                self.from_tx = from_tx
            else:
                self.hash = Sha256Hash.ZERO_HASH

    def __str__(self):
        return f"{self.hash}:{self.index}"
