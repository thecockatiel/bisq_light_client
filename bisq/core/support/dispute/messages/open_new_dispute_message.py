from dataclasses import dataclass
from typing import TYPE_CHECKING
from bisq.core.support.dispute.messages.dispute_message import DisputeMessage
from bisq.core.support.support_type import SupportType
from bisq.core.network.p2p.node_address import NodeAddress
import proto.pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.support.dispute.dispute import Dispute
    from bisq.core.protocol.core_proto_resolver import CoreProtoResolver


@dataclass(kw_only=True)
class OpenNewDisputeMessage(DisputeMessage):
    dispute: "Dispute"
    sender_node_address: "NodeAddress"

    def to_proto_network_envelope(self):
        envelope = self.get_network_envelope_builder()
        envelope.open_new_dispute_message.CopyFrom(
            protobuf.OpenNewDisputeMessage(
                uid=self.uid,
                dispute=self.dispute.to_proto_message(),
                sender_node_address=self.sender_node_address.to_proto_message(),
                type=SupportType.to_proto_message(self.support_type),
            )
        )
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.OpenNewDisputeMessage, core_proto_resolver: "CoreProtoResolver", message_version: int):
        from bisq.core.support.dispute.dispute import Dispute
        
        return OpenNewDisputeMessage(
            dispute=Dispute.from_proto(proto.dispute, core_proto_resolver),
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            uid=proto.uid,
            support_type=SupportType.from_proto(proto.type),
            message_version=message_version,
        )

    @property
    def trade_id(self):
        return self.dispute.trade_id

    def __str__(self):
        return (
            f"OpenNewDisputeMessage("
            f"\n     dispute={self.dispute}"
            f",\n     sender_node_address={self.sender_node_address}"
            f",\n     OpenNewDisputeMessage.uid='{self.uid}'"
            f",\n     message_version={self.message_version}"
            f",\n     support_type={self.support_type}"
            f"\n) {super().__str__()}"
        )
