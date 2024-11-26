from dataclasses import dataclass
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.support.dispute.arbitration.messages.arbitration_message import ArbitrationMessage
from bisq.core.support.support_type import SupportType
import proto.pb_pb2 as protobuf

@dataclass(kw_only=True)
class PeerPublishedDisputePayoutTxMessage(ArbitrationMessage):
    transaction: bytes
    trade_id: str
    sender_node_address: NodeAddress

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        envelope = self.get_network_envelope_builder()
        envelope.peer_published_dispute_payout_tx_message.CopyFrom(
             protobuf.PeerPublishedDisputePayoutTxMessage(
                transaction=self.transaction,
                trade_id=self.trade_id,
                sender_node_address=self.sender_node_address.to_proto_message(),
                uid=self.uid,
                type=SupportType.to_proto_message(self.support_type),
             )
        )
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.PeerPublishedDisputePayoutTxMessage, message_version: int):
        return PeerPublishedDisputePayoutTxMessage(
            message_version=message_version,
            uid=proto.uid,
            support_type=SupportType.from_proto(proto.type),
            transaction=proto.transaction,
            trade_id=proto.trade_id,
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
        )

    def get_trade_id(self) -> str:
        return self.trade_id

    def __str__(self) -> str:
        return (
            f"PeerPublishedDisputePayoutTxMessage{{\n"
            f"     transaction={self.transaction.hex()},\n"
            f"     trade_id='{self.trade_id}',\n"
            f"     sender_node_address={self.sender_node_address},\n"
            f"     uid='{self.uid}',\n"
            f"     message_version={self.message_version},\n"
            f"     support_type={self.support_type}\n"
            f"}} {super().__str__()}"
        )