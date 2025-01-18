from dataclasses import dataclass, field

from bisq.core.network.p2p.storage.messages.broadcast_message import BroadcastMessage
from bisq.core.network.p2p.storage.payload.protected_mailbox_storage_entry import (
    ProtectedMailboxStorageEntry,
)
import proto.pb_pb2 as protobuf

from typing import TYPE_CHECKING

from utils.data import raise_required

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_proto_resolver import (
        NetworkProtoResolver,
    )


@dataclass
class RemoveMailboxDataMessage(BroadcastMessage):
    protected_mailbox_storage_entry: ProtectedMailboxStorageEntry = field(default_factory=raise_required)

    # PROTO BUFFER
    def to_proto_network_envelope(self):
        envelope = self.get_network_envelope_builder()
        envelope.remove_mailbox_data_message.CopyFrom(
            protobuf.RemoveMailboxDataMessage(
                protected_storage_entry=self.protected_mailbox_storage_entry.to_proto_message()
            )
        )
        return envelope

    @staticmethod
    def from_proto(
        proto: "protobuf.RemoveMailboxDataMessage",
        resolver: "NetworkProtoResolver",
        message_version: int,
    ):
        return RemoveMailboxDataMessage(
            message_version=message_version,
            protected_mailbox_storage_entry=ProtectedMailboxStorageEntry.from_proto(
                proto.protected_storage_entry, resolver
            ),
        )
        
    def __hash__(self):
        return hash(self.protected_mailbox_storage_entry)
