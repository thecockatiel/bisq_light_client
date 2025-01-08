from typing import TYPE_CHECKING, Optional

from electrum_min.transaction import TxOutpoint


if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.core.transaction_output import TransactionOutput


# TODO
class TransactionOutPoint:
    MESSAGE_LENGTH = 36

    def __init__(
        self,
        index: int,
        hash: str,
        from_tx: Optional["Transaction"] = None,
        connected_output: Optional["TransactionOutput"] = None,
    ):
        self.connected_output = connected_output
        self.from_tx = from_tx
        self.index = index
        self.hash = hash

    @property
    def length(self):
        return TransactionOutPoint.MESSAGE_LENGTH

    @staticmethod
    def from_tx_output(tx_output: "TransactionOutput"):
        return TransactionOutPoint(
            tx_output.index,
            tx_output.parent.get_tx_id(),
            from_tx=tx_output.parent,
            connected_output=tx_output,
        )

    def to_electrum_tx_output(self):
        return TxOutpoint(self.hash, self.index)

    def __str__(self):
        return f"{self.hash}:{self.index}"

    def __hash__(self):
        return hash((self.hash, self.index))

    def __eq__(self, value):
        if isinstance(value, TransactionOutPoint):
            return self.hash == value.hash and self.index == value.index
        if isinstance(value, TxOutpoint):
            return self.hash == value.txid.hex() and self.index == value.out_idx
        return False