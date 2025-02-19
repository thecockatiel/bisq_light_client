from typing import TYPE_CHECKING, Optional
from bisq.core.dao.state.model.blockchain.base_tx import BaseTx
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bisq.core.dao.node.parser.temp_tx_output import TempTxOutput

if TYPE_CHECKING:
    from bisq.core.dao.state.model.blockchain.tx_input import TxInput
    from bisq.core.dao.node.full.raw_tx import RawTx


class TempTx(BaseTx):
    """
    Used only temporary during the transaction parsing process to support mutable data while parsing.
    After parsing it will get cloned to the immutable Tx.
    We don't need to implement the ProtoBuffer methods as it is not persisted or sent over the wire.
    """

    def __init__(
        self,
        tx_version: str,
        tx_id: str,
        block_height: int,
        block_hash: str,
        time: int,
        tx_inputs: tuple["TxInput"],
        temp_tx_outputs: tuple["TempTxOutput"],
        tx_type: Optional[TxType],
        burnt_bsq: int,
    ):
        super().__init__(tx_version, tx_id, block_height, block_hash, time, tx_inputs)
        self.temp_tx_outputs = temp_tx_outputs
        # Mutable data:
        self.tx_type = tx_type
        self.burnt_bsq = burnt_bsq

    @staticmethod
    def from_raw_tx(raw_tx: "RawTx") -> "TempTx":
        return TempTx(
            raw_tx.tx_version,
            raw_tx.id,
            raw_tx.block_height,
            raw_tx.block_hash,
            raw_tx.time,
            raw_tx.tx_inputs,
            tuple(
                TempTxOutput.from_raw_tx_output(output)
                for output in raw_tx.raw_tx_outputs
            ),
            None,
            0,
        )

    def __str__(self):
        return (
            f"TempTx{{\n"
            f"     temp_tx_outputs={self.temp_tx_outputs},\n"
            f"     tx_type={self.tx_type},\n"
            f"     burnt_bsq={self.burnt_bsq}\n"
            f"}} " + super().__str__()
        )

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, TempTx):
            return False
        if not super().__eq__(other):
            return False
        return (
            self.burnt_bsq == other.burnt_bsq
            and self.temp_tx_outputs == other.temp_tx_outputs
            and (self.tx_type.name if self.tx_type else "")
            == (other.tx_type.name if other.tx_type else "")
        )

    def __hash__(self):
        return hash(
            (
                super().__hash__(),
                self.temp_tx_outputs,
                self.tx_type.name if self.tx_type else None,
                self.burnt_bsq,
            )
        )
