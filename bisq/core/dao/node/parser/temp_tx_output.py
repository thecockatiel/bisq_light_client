from typing import TYPE_CHECKING, Optional
from bisq.core.dao.state.model.blockchain.base_tx_output import BaseTxOutput
from bisq.core.dao.state.model.blockchain.pub_key_script import PubKeyScript
from bisq.core.dao.state.model.blockchain.tx_output_type import TxOutputType

if TYPE_CHECKING:
    from bisq.core.dao.node.full.raw_tx_output import RawTxOutput


class TempTxOutput(BaseTxOutput):
    """
    Contains mutable BSQ specific data (TxOutputType) and used only during tx parsing.
    Will get converted to immutable TxOutput after tx parsing is completed.
    """

    def __init__(
        self,
        index: int,
        value: int,
        tx_id: str,
        pub_key_script: Optional[PubKeyScript],
        address: Optional[str],
        op_return_data: Optional[bytes],
        block_height: int,
        tx_output_type: TxOutputType,
        lock_time: int,
        unlock_block_height: int,
    ):
        super().__init__(
            index, value, tx_id, pub_key_script, address, op_return_data, block_height
        )
        self.tx_output_type = tx_output_type
        # The lockTime is stored in the first output of the LOCKUP tx.
        # If not set it is -1, 0 is a valid value.
        self.lock_time = lock_time
        # The unlockBlockHeight is stored in the first output of the UNLOCK tx.
        self.unlock_block_height = unlock_block_height

    @staticmethod
    def from_raw_tx_output(tx_output: "RawTxOutput") -> "TempTxOutput":
        return TempTxOutput(
            tx_output.index,
            tx_output.value,
            tx_output.tx_id,
            tx_output.pub_key_script,
            tx_output.address,
            tx_output.op_return_data,
            tx_output.block_height,
            TxOutputType.UNDEFINED_OUTPUT,
            -1,
            0,
        )

    @property
    def is_op_return_output(self) -> bool:
        # We do not check for pubKeyScript.scriptType.NULL_DATA because that is only set if dumpBlockchainData is true
        return self.op_return_data is not None

    def __str__(self) -> str:
        return (
            f"TempTxOutput{{\n"
            f"    tx_output_type={self.tx_output_type.name},\n"
            f"    lock_time={self.lock_time},\n"
            f"    unlock_block_height={self.unlock_block_height}\n"
            f"}} {super().__str__()}"
        )

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, TempTxOutput):
            return False
        if not super().__eq__(other):
            return False
        return (
            self.lock_time == other.lock_time
            and self.unlock_block_height == other.unlock_block_height
            and self.tx_output_type.name == other.tx_output_type.name
        )

    def __hash__(self) -> int:
        return hash(
            (
                super().__hash__(),
                self.tx_output_type.name,
                self.lock_time,
                self.unlock_block_height,
            )
        )
