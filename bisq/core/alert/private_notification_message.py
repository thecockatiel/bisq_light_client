from dataclasses import dataclass, field
from datetime import timedelta
from typing import ClassVar
import uuid

from bisq.core.alert.private_notification_payload import PrivateNotificationPayload
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.mailbox.mailbox_message import MailboxMessage 
from bisq.core.network.p2p.node_address import NodeAddress
import proto.pb_pb2 as protobuf


@dataclass(kw_only=True)
class PrivateNotificationMessage(NetworkEnvelope, MailboxMessage):
    TTL: ClassVar[int] = int(timedelta(days=30).total_seconds() * 1000)

    private_notification_payload: PrivateNotificationPayload
    sender_node_address: NodeAddress
    uid: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        envelope = self.get_network_envelope_builder()
        envelope.private_notification_message.CopyFrom(
            protobuf.PrivateNotificationMessage(
                private_notification_payload=self.private_notification_payload.to_proto_message(),
                sender_node_address=self.sender_node_address,
                uid=self.uid,
            )
        )
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.PrivateNotificationMessage, message_version: int):
        return PrivateNotificationMessage(
            message_version=message_version,
            private_notification_payload=PrivateNotificationPayload.from_proto(
                proto.private_notification_payload
            ),
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            uid=proto.uid,
        )

    def get_ttl(self) -> int:
        return self.TTL
