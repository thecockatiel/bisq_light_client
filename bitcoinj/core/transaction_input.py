from typing import TYPE_CHECKING, Optional
from bitcoinj.core.transaction_out_point import TransactionOutPoint
from bitcoinj.core.transaction_output import TransactionOutput

if TYPE_CHECKING:
    from electrum_min.transaction import TxInput as ElectrumTxInput
    from bitcoinj.core.transaction import Transaction


# TODO
class TransactionInput:
    def __init__(self, tx: "Transaction", ec_tx_input: "ElectrumTxInput", index: int):
        self.parent = tx
        self._ec_tx_input = ec_tx_input
        self.index = index
        self.outpoint = TransactionOutPoint(TransactionOutput(tx, tx._electrum_transaction.outputs()[index], index))

    @property
    def connected_transaction(self) -> Optional["Transaction"]:
        return self.outpoint.from_tx if self.outpoint else None

    @property
    def connected_output(self) -> Optional["TransactionOutput"]:
        return self.outpoint.connected_output if self.outpoint else None
    
    @property
    def nsequence(self) -> int:
        return self._ec_tx_input.nsequence
    
    @property
    def has_witness(self) -> bool:
        return self._ec_tx_input.witness is not None and self._ec_tx_input.witness != b'\x00'
