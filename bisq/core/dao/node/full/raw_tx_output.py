from typing import TYPE_CHECKING, Optional
from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.dao.state.model.blockchain.base_tx_output import BaseTxOutput
import pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.dao.state.model.blockchain.tx_output import TxOutput


class RawTxOutput(BaseTxOutput, NetworkPayload):
    """
    TxOutput used in RawTx. Containing only immutable bitcoin specific fields.
    Sent over wire.
    """

    def __init__(
        self,
        index: int,
        value: int,
        tx_id: str,
        pub_key_script: Optional[str],
        address: Optional[str],
        op_return_data: Optional[bytes],
        block_height: int,
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

    @staticmethod
    def from_tx_output(tx_output: "TxOutput") -> "RawTxOutput":
        return RawTxOutput(
            tx_output.index,
            tx_output.value,
            tx_output.tx_id,
            tx_output.pub_key_script,
            tx_output.address,
            tx_output.op_return_data,
            tx_output.block_height,
        )

    def to_proto_message(self):
        builder = self.get_raw_tx_output_builder()
        builder.raw_tx_output.CopyFrom(protobuf.RawTxOutput())
        return builder

    @staticmethod
    def from_proto(proto: protobuf.BaseTxOutput) -> "RawTxOutput":
        return RawTxOutput(
            proto.index,
            proto.value,
            proto.tx_id,
            proto.pub_key_script if proto.HasField("pub_key_script") else None,
            proto.address if proto.address else None,
            proto.op_return_data if proto.op_return_data else None,
            proto.block_height,
        )

    def __str__(self):
        return (
            f"RawTxOutput{{\n"
            f"    index={self.index},\n"
            f"    value={self.value},\n"
            f"    tx_id='{self.tx_id}',\n"
            f"    pub_key_script={self.pub_key_script},\n"
            f"    address='{self.address}',\n"
            f"    op_return_data={bytes_as_hex_string(self.op_return_data)},\n"
            f"    block_height={self.block_height}\n"
            f"}}"
        )
