from typing import TYPE_CHECKING
from bisq.core.trade.protocol.trade_message import TradeMessage
import pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.network.p2p.node_address import NodeAddress


class BsqSwapFinalizedTxMessage(TradeMessage):
    def __init__(
        self,
        trade_id: str,
        sender_node_address: "NodeAddress",
        tx: bytes,
        uid: str = None,
        message_version: int = None,
    ):
        super_kwargs = {
            "message_version": message_version,
            "trade_id": trade_id,
            "uid": uid,
        }
        # filter out the none values from the super to allow default values to be used
        super_kwargs = {k: v for k, v in super_kwargs.items() if v is not None}
        super().__init__(**super_kwargs)
        self.sender_node_address = sender_node_address
        self.tx = tx

    def to_proto_message(self):
        return protobuf.BsqSwapFinalizedTxMessage(
            uid=self.uid,
            trade_id=self.trade_id,
            sender_node_address=self.sender_node_address.to_proto_message(),
            tx=self.tx,
        )

    def to_proto_network_envelope(self):
        builder = self.get_network_envelope_builder()
        builder.bsq_swap_finalized_tx_message.CopyFrom(self.to_proto_message())
        return builder

    @staticmethod
    def from_proto(proto: protobuf.BsqSwapFinalizedTxMessage, message_version: int):
        return BsqSwapFinalizedTxMessage(
            message_version=message_version,
            trade_id=proto.trade_id,
            uid=proto.uid,
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            tx=proto.tx,
        )

    def __eq__(self, other):
        return (
            isinstance(other, BsqSwapFinalizedTxMessage)
            and super().__eq__(other)
            and self.sender_node_address == other.sender_node_address
            and self.tx == other.tx
        )

    def __hash__(self):
        return hash((super().__hash__(), self.sender_node_address, self.tx))
