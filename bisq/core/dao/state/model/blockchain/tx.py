from typing import Optional, Union
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.dao.node.parser.temp_tx import TempTx
from bisq.core.dao.state.model.blockchain.base_tx import BaseTx
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
from bisq.core.dao.state.model.blockchain.tx_input import TxInput
from bisq.core.dao.state.model.blockchain.tx_output import TxOutput
import pb_pb2 as protobuf


class Tx(BaseTx, PersistablePayload, ImmutableDaoStateModel):
    """
    Immutable class for a Bsq transaction.
    Gets persisted.
    """

    def __init__(
        self,
        tx_version: str,
        tx_id: str,
        block_height: int,
        block_hash: str,
        time: int,
        tx_inputs: tuple[TxInput],
        tx_outputs: Union[tuple[TxOutput],tuple[TxOutput,TxOutput,TxOutput,TxOutput]],
        tx_type: Optional[TxType],
        burnt_bsq: int,
    ):
        super().__init__(
            tx_version,
            tx_id,
            block_height,
            block_hash,
            time,
            tx_inputs,
        )
        self.tx_outputs = tx_outputs
        self.tx_type = tx_type
        # Can be burned fee or in case of an invalid tx the burned BSQ from all BSQ inputs
        self.burnt_bsq = burnt_bsq

    # Created after parsing of a tx is completed. We store only the immutable tx in the block.
    @staticmethod
    def from_temp_tx(temp_tx: TempTx):
        tx_outputs = tuple(
            TxOutput.from_temp_output(output) for output in temp_tx.temp_tx_outputs
        )
        return Tx(
            temp_tx.tx_version,
            temp_tx.id,
            temp_tx.block_height,
            temp_tx.block_hash,
            temp_tx.time,
            temp_tx.tx_inputs,
            tx_outputs,
            temp_tx.tx_type,
            temp_tx.burnt_bsq,
        )

    def to_proto_message(self):
        builder = self.get_base_tx_builder()
        builder.tx.CopyFrom(
            protobuf.Tx(
                tx_outputs=[output.to_proto_message() for output in self.tx_outputs],
                txType=(
                    self.tx_type.to_proto_message() if self.tx_type else None
                ),  # weird protobuf names
                burnt_bsq=self.burnt_bsq,
            )
        )
        return builder

    @staticmethod
    def from_proto(proto: protobuf.BaseTx):
        tx_inputs = tuple(TxInput.from_proto(input) for input in proto.tx_inputs)
        proto_tx = proto.tx
        tx_outputs = tuple(
            TxOutput.from_proto(output) for output in proto_tx.tx_outputs
        )
        return Tx(
            proto.tx_version,
            proto.id,
            proto.block_height,
            proto.block_hash,
            proto.time,
            tx_inputs,
            tx_outputs,
            TxType.from_proto(proto_tx.txType),
            proto_tx.burnt_bsq,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Utils
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @property
    def last_tx_output(self) -> TxOutput:
        return self.tx_outputs[-1]

    @property
    def burnt_fee(self) -> int:
        return 0 if self.tx_type == TxType.INVALID else self.burnt_bsq

    @property
    def invalidated_bsq(self) -> int:
        return self.burnt_bsq if self.tx_type == TxType.INVALID else 0

    @property
    def lock_time(self) -> int:
        return self.lockup_output.lock_time

    @property
    def locked_amount(self) -> int:
        return self.lockup_output.value

    @property
    def lockup_output(self) -> TxOutput:
        # The lockTime is stored in the first output of the LOCKUP tx.
        return self.tx_outputs[0]

    @property
    def unlock_block_height(self) -> int:
        # The unlockBlockHeight is stored in the first output of the UNLOCK tx.
        return self.lockup_output.unlock_block_height

    def __str__(self) -> str:
        return (
            f"Tx{{\n"
            f"     tx_outputs={self.tx_outputs},\n"
            f"     tx_type={self.tx_type},\n"
            f"     burnt_bsq={self.burnt_bsq}\n"
            f"}} {super().__str__()}"
        )

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, Tx):
            return False
        if not super().__eq__(other):
            return False

        is_tx_type_equals = (self.tx_type.name if self.tx_type else "") == (
            other.tx_type.name if other.tx_type else ""
        )

        return (
            self.burnt_bsq == other.burnt_bsq
            and self.tx_outputs == other.tx_outputs
            and is_tx_type_equals
        )

    def __hash__(self):
        return hash(
            (
                super().__hash__(),
                self.tx_outputs,
                self.tx_type.name if self.tx_type else "",
                self.burnt_bsq,
            )
        )
