from typing import TYPE_CHECKING
from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.core.dao.state.model.blockchain.base_tx import BaseTx
import pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.dao.state.model.blockchain.tx import Tx
    from bisq.core.dao.state.model.blockchain.tx_input import TxInput
    from bisq.core.dao.node.full.raw_tx_output import RawTxOutput


class RawTx(BaseTx, NetworkPayload):
    """
    RawTx as we get it from the RPC service (full node) or from via the P2P network (lite node).
    It contains pure bitcoin blockchain data without any BSQ specific data.
    Sent over wire.
    """

    # The RPC service is creating a RawTx.
    def __init__(
        self,
        id: str,
        block_height: int,
        block_hash: str,
        time: int,
        tx_inputs: tuple["TxInput"],
        raw_tx_outputs: tuple["RawTxOutput"],
    ):
        super().__init__(id, block_height, block_hash, time, tx_inputs)
        self.raw_tx_outputs = raw_tx_outputs

    # Used when a full node sends a block over the P2P network
    @staticmethod
    def from_tx(tx: "Tx") -> "RawTx":
        raw_tx_outputs = tuple(
            RawTxOutput.from_tx_output(output) for output in tx.tx_outputs
        )
        return RawTx(
            id=tx.id,
            block_height=tx.block_height,
            block_hash=tx.block_hash,
            time=tx.time,
            tx_inputs=tx.tx_inputs,
            raw_tx_outputs=raw_tx_outputs,
        )

    def to_proto_message(self):
        builder = self.get_base_tx_builder()
        builder.raw_tx.CopyFrom(
            protobuf.RawTx(
                raw_tx_outputs=[
                    output.to_proto_message() for output in self.raw_tx_outputs
                ]
            )
        )
        return builder

    @staticmethod
    def from_proto(proto_base_tx: protobuf.BaseTx) -> "RawTx":
        tx_inputs = tuple(
            TxInput.from_proto(input) for input in proto_base_tx.tx_inputs
        )
        proto_raw_tx = proto_base_tx.raw_tx
        raw_tx_outputs = tuple(
            RawTxOutput.from_proto(output) for output in proto_raw_tx.raw_tx_outputs
        )
        return RawTx(
            id=proto_base_tx.id,
            block_height=proto_base_tx.block_height,
            block_hash=proto_base_tx.block_hash,
            time=proto_base_tx.time,
            tx_inputs=tx_inputs,
            raw_tx_outputs=raw_tx_outputs,
        )

    def __str__(self):
        return (
            f"RawTx{{\n"
            f"    id='{self.id}',\n"
            f"    block_height={self.block_height},\n"
            f"    block_hash='{self.block_hash}',\n"
            f"    time={self.time},\n"
            f"    tx_inputs={self.tx_inputs},\n"
            f"    raw_tx_outputs={self.raw_tx_outputs}\n"
            f"}}"
        )
