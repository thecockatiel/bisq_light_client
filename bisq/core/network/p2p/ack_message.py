# TODO ExpirablePayload has no effect here as it is either a direct msg or packed into MailboxStoragePayload
# We could extend the TTL by setting the TTL in MailboxStoragePayload from the type of msg which gets into the
# SealedAndSigned data.

# We exclude uid from hashcode and equals to detect duplicate entries of the same AckMessage
from dataclasses import dataclass, field
from typing import Optional
import uuid

from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.common.protocol.proto_util import ProtoUtil
from bisq.core.network.p2p.ack_message_source_type import AckMessageSourceType
from bisq.core.network.p2p.node_address import NodeAddress
import proto.pb_pb2 as protobuf

@dataclass(frozen=True, kw_only=True)
class AckMessage(NetworkEnvelope):
    TTL: int = 7 * 24 * 60 * 60 * 1000 # 604800000 ms or 7 days

    uid: str = field(default_factory=lambda: str(uuid.uuid4()), init=False)
    sender_node_address: NodeAddress
    source_type: AckMessageSourceType
    source_msg_class_name: str
    source_uid: Optional[str]
    source_id: str
    success: bool
    error_message: Optional[str]

    # PROTO BUFFER
    def to_proto_message(self) -> protobuf.AckMessage:
        message =  protobuf.AckMessage(
            uid=self.uid,
            sender_node_address=self.sender_node_address.to_proto_message(),
            source_type=self.source_type.name,
            source_msg_class_name=self.source_msg_class_name,
            source_id=self.source_id,
            success=self.success,
        )
        if self.source_uid is not None:
            message.source_uid = self.source_uid
        if self.error_message is not None:
            message.error_message = self.error_message
        return message

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        envelope = self.get_network_envelope_builder()
        envelope.ack_message.CopyFrom(self.to_proto_message())
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.AckMessage, message_version: int) -> 'AckMessage':
        source_type = ProtoUtil.enum_from_proto(AckMessageSourceType, proto.source_type) 
        return AckMessage(
            uid=proto.uid,
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            source_type=source_type,
            source_msg_class_name=proto.source_msg_class_name,
            source_uid=proto.source_uid,
            source_id=proto.source_id,
            success=proto.success,
            error_message=proto.error_message,
            message_version=message_version
        )

    # API
    def get_ttl(self) -> int:
        return self.TTL

    def __str__(self):
        return (f"AckMessage{{\n     uid='{self.uid}',"
                f"\n     sender_node_address={self.sender_node_address},"
                f"\n     source_type={self.source_type},"
                f"\n     source_msg_class_name='{self.source_msg_class_name}',"
                f"\n     source_uid='{self.source_uid}',"
                f"\n     source_id='{self.source_id}',"
                f"\n     success={self.success},"
                f"\n     error_message='{self.error_message}'\n}} {super().__str__()}")