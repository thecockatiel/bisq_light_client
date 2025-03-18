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
        self._connected_output = connected_output
        self._connected_tx = from_tx
        self._index = index
        self._hash = hash

    @property
    def connected_output(self):
        return self._connected_output

    @property
    def connected_tx(self):
        return self._connected_tx

    @property
    def index(self):
        """Which output of that transaction we are talking about."""
        return self._index

    @property
    def hash(self):
        """Hash of the transaction to which we refer."""
        return self._hash

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

    @staticmethod
    def from_tx(tx: "Transaction", index: int):
        return TransactionOutPoint(
            index, tx.get_tx_id(), from_tx=tx, connected_output=tx.outputs[index]
        )

    def to_electrum_tx_output(self):
        return TxOutpoint(bytes.fromhex(self._hash), self._index)

    def __str__(self):
        return f"{self._hash}:{self._index}"

    def __hash__(self):
        return hash((self._hash, self._index))

    def __eq__(self, value):
        if isinstance(value, TransactionOutPoint):
            return self._hash == value._hash and self._index == value.index
        if isinstance(value, TxOutpoint):
            return self._hash == value.txid.hex() and self._index == value.out_idx
        return False
