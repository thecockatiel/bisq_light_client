from typing import TYPE_CHECKING, Optional


if TYPE_CHECKING:
    from bitcoinj.core.transaction_output import TransactionOutput


# TODO
class TransactionOutPoint:
    MESSAGE_LENGTH = 36

    def __init__(self, tx_output: "TransactionOutput"):
        self.connected_output = tx_output
        self.from_tx = tx_output.parent
        self.index = tx_output.index
        self.length = TransactionOutPoint.MESSAGE_LENGTH
        
    @property
    def hash(self):
        return self.from_tx.get_tx_id()

    def __str__(self):
        return f"{self.hash}:{self.index}"
