from dataclasses import dataclass, field

from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.support.dispute.dispute_result import DisputeResult
from bisq.core.support.dispute.messages.dispute_message import DisputeMessage
from bisq.core.support.support_type import SupportType 
import proto.pb_pb2 as protobuf
from utils.data import raise_required

@dataclass
class DisputeResultMessage(DisputeMessage):
    dispute_result: DisputeResult = field(default_factory=raise_required)
    sender_node_address: NodeAddress = field(default_factory=raise_required)

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        envelope = self.get_network_envelope_builder()
        envelope.dispute_result_message.CopyFrom(protobuf.DisputeResultMessage(
            dispute_result=self.dispute_result.to_proto_message(),
            sender_node_address=self.sender_node_address.to_proto_message(),
            uid=self.uid,
            type=SupportType.to_proto_message(self.support_type),
        )) 
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.DisputeResultMessage, message_version: int) -> 'DisputeResultMessage':
        assert proto.HasField('dispute_result'), "DisputeResult must be set"
        return DisputeResultMessage(
            message_version=message_version,
            dispute_result=DisputeResult.from_proto(proto.dispute_result),
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            uid=proto.uid,
            support_type=SupportType.from_proto(proto.type),
        )

    def get_trade_id(self) -> str:
        return self.dispute_result.trade_id

    def __str__(self) -> str:
        return (f"DisputeResultMessage{{\n"
                f"     disputeResult={self.dispute_result},\n"
                f"     senderNodeAddress={self.sender_node_address},\n"
                f"     DisputeResultMessage.uid='{self.uid}',\n"
                f"     messageVersion={self.message_version},\n"
                f"     supportType={self.support_type}\n"
                f"}} {super().__str__()}")