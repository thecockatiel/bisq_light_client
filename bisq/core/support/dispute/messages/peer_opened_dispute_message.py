from dataclasses import dataclass

from bisq.core.network.p2p.network.core_proto_resolver import CoreProtoResolver
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.support.dispute.dispute import Dispute
from bisq.core.support.dispute.messages.dispute_message import DisputeMessage
from bisq.core.support.support_type import SupportType
import proto.pb_pb2 as protobuf


@dataclass(kw_only=True)
class PeerOpenedDisputeMessage(DisputeMessage):
    dispute: Dispute
    sender_node_address: NodeAddress

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        envelope = self.get_network_envelope_builder()
        envelope.peer_opened_dispute_message.CopyFrom(
            protobuf.PeerOpenedDisputeMessage(
                uid=self.uid,
                dispute=self.dispute.to_proto_message(),
                sender_node_address=self.sender_node_address.to_proto_message(),
                type=SupportType.to_proto_message(self.support_type),
            )
        )
        return envelope

    @staticmethod
    def from_proto(
        proto: protobuf.PeerOpenedDisputeMessage, core_proto_resolver: CoreProtoResolver, message_version: int
    ) -> "PeerOpenedDisputeMessage":
        return PeerOpenedDisputeMessage(
            message_version=message_version,
            uid=proto.uid,
            support_type=SupportType.from_proto(proto.type),
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            dispute=Dispute.from_proto(proto.dispute, core_proto_resolver),
        )

    def get_trade_id(self) -> str:
        return self.dispute.get_trade_id()

    def __str__(self) -> str:
        return (
            f"PeerOpenedDisputeMessage("
            f"\n     dispute={self.dispute}"
            f",\n     sender_node_address={self.sender_node_address}"
            f",\n     uid='{self.uid}'"
            f",\n     message_version={self.message_version}"
            f",\n     support_type={self.support_type}"
            f"\n) {super().__str__()}"
        )
