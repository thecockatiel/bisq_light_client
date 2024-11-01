from dataclasses import dataclass, field

from bisq.core.network.p2p.storage.messages.broadcast_message import BroadcastMessage
from bisq.core.network.p2p.storage.payload.protected_mailbox_storage_entry import ProtectedMailboxStorageEntry
import bisq.core.common.version as Version
import proto.pb_pb2 as protobuf

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.core.common.protocol.network.network_proto_resolver import NetworkProtoResolver    

@dataclass(frozen=True)
class RemoveMailboxDataMessage(BroadcastMessage):
    protected_storage_entry: ProtectedMailboxStorageEntry

    def __init__(self, protected_storage_entry: ProtectedMailboxStorageEntry, message_version: int = Version.get_p2p_message_version()):
        super().__init__(message_version)
        self.protected_storage_entry = protected_storage_entry

    # PROTO BUFFER
    def to_proto_network_envelope(self):
        envelope = self.get_network_envelope_builder()
        envelope.remove_mailbox_data_message = protobuf.RemoveMailboxDataMessage(
            protected_storage_entry = self.protected_storage_entry.to_proto_message()
        )
        return envelope

    @staticmethod
    def from_proto(proto: 'protobuf.RemoveMailboxDataMessage', resolver: 'NetworkProtoResolver', message_version: int):
        return RemoveMailboxDataMessage(ProtectedMailboxStorageEntry.from_proto(proto.protected_storage_entry, resolver), message_version)
