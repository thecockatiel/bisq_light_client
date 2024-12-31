from typing import TYPE_CHECKING, Optional
from bitcoinj.base.coin import Coin
from bitcoinj.core.transaction_out_point import TransactionOutPoint
from bitcoinj.core.transaction_output import TransactionOutput

if TYPE_CHECKING:
    from electrum_min.transaction import TxInput as ElectrumTxInput
    from bitcoinj.core.transaction import Transaction


# TODO
class TransactionInput:
    NO_SEQUENCE = 0xFFFFFFFF
    SEQUENCE_LOCKTIME_DISABLE_FLAG = 1 < 31
    
    def __init__(self, tx: "Transaction", ec_tx_input: "ElectrumTxInput", index: int):
        self.parent = tx
        self._ec_tx_input = ec_tx_input
        self.index = index
        output = TransactionOutput(tx, tx._electrum_transaction.outputs()[index], index)
        self.outpoint = TransactionOutPoint(output)
        self.value = output.get_value()

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
    def has_sequence(self) -> bool:
        return self.nsequence != TransactionInput.NO_SEQUENCE
    
    @property
    def witness(self) -> Optional[str]:
        return self._ec_tx_input.witness.hex() if self.has_witness else None
    
    @property
    def has_witness(self) -> bool:
        return self._ec_tx_input.is_segwit()

    @property
    def has_relative_lock_time(self) -> bool:
        return self.nsequence & TransactionInput.SEQUENCE_LOCKTIME_DISABLE_FLAG == 0
    
    @property
    def is_opt_in_full_rbf(self) -> bool:
        return self.nsequence < TransactionInput.NO_SEQUENCE - 1
    
    @property
    def is_coin_base(self) -> bool:
        return self._ec_tx_input.is_coinbase_input()
    
    @property
    def script_sig(self) -> Optional[bytes]:
        return self._ec_tx_input.script_sig
