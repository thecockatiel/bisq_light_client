from typing import TYPE_CHECKING, Optional
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.dao.state.model.blockchain.base_tx_output import BaseTxOutput
from bisq.core.dao.state.model.blockchain.tx_output_type import TxOutputType
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
import pb_pb2 as protobuf


if TYPE_CHECKING:
    from bisq.core.dao.node.parser.temp_tx_output import TempTxOutput


class TxOutput(BaseTxOutput, PersistablePayload, ImmutableDaoStateModel):

    def __init__(
        self,
        index: int,
        value: int,
        tx_id: str,
        pub_key_script: Optional[str],
        address: Optional[str],
        op_return_data: Optional[bytes],
        block_height: int,
        tx_output_type: TxOutputType,
        lock_time: int,
        unlock_block_height: int,
    ):
        super().__init__(
            index,
            value,
            tx_id,
            pub_key_script,
            address,
            op_return_data,
            block_height,
        )
        self.tx_output_type = tx_output_type
        # The lockTime is stored in the first output of the LOCKUP tx.
        # If not set it is -1, 0 is a valid value.
        self.lock_time = lock_time
        # The unlockBlockHeight is stored in the first output of the UNLOCK tx.
        self.unlock_block_height = unlock_block_height

    @staticmethod
    def from_temp_output(temp_tx_output: "TempTxOutput") -> "TxOutput":
        return TxOutput(
            temp_tx_output.index,
            temp_tx_output.value,
            temp_tx_output.tx_id,
            temp_tx_output.pub_key_script,
            temp_tx_output.address,
            temp_tx_output.op_return_data,
            temp_tx_output.block_height,
            temp_tx_output.tx_output_type,
            temp_tx_output.lock_time,
            temp_tx_output.unlock_block_height,
        )

    def to_proto_message(self):
        builder = self.get_raw_tx_output_builder()
        builder.tx_output.CopyFrom(
            protobuf.TxOutput(
                tx_output_type=self.tx_output_type.to_proto_message(),
                lock_time=self.lock_time,
                unlock_block_height=self.unlock_block_height,
            )
        )
        return builder

    @staticmethod
    def from_proto(proto: protobuf.BaseTxOutput) -> "TxOutput":
        proto_tx_output = proto.tx_output
        return TxOutput(
            proto.index,
            proto.value,
            proto.tx_id,
            proto.pub_key_script if proto.HasField("pub_key_script") else None,
            proto.address if proto.address else None,
            proto.op_return_data if proto.op_return_data else None,
            proto.block_height,
            TxOutputType.from_proto(proto_tx_output.tx_output_type),
            proto_tx_output.lock_time,
            proto_tx_output.unlock_block_height,
        )

    def __str__(self):
        return (
            f"TxOutput{{\n"
            f"    txOutputType={self.tx_output_type.name},\n"
            f"    lockTime={self.lock_time},\n"
            f"    unlockBlockHeight={self.unlock_block_height}\n"
            f"}} {super().__str__()}"
        )

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, TxOutput):
            return False
        if not super().__eq__(other):
            return False
        return (
            self.lock_time == other.lock_time
            and self.unlock_block_height == other.unlock_block_height
            and self.tx_output_type.name == other.tx_output_type.name
        )

    def __hash__(self):
        return hash(
            (
                super().__hash__(),
                self.tx_output_type.name,
                self.lock_time,
                self.unlock_block_height,
            )
        )
