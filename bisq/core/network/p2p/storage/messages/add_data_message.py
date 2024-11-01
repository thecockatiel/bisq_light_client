from dataclasses import dataclass
from typing import cast
from bisq.core.common.protocol.network.network_proto_resolver import NetworkProtoResolver
from bisq.core.network.p2p.storage.messages.broadcast_message import BroadcastMessage
from bisq.core.network.p2p.storage.payload.protected_mailbox_storage_entry import ProtectedMailboxStorageEntry
from bisq.core.network.p2p.storage.payload.protected_storage_entry import ProtectedStorageEntry
import proto.pb_pb2 as protobuf
from google.protobuf.message import Message
import bisq.core.common.version as Version

@dataclass(frozen=True)
class AddDataMessage(BroadcastMessage):
    protected_storage_entry: ProtectedStorageEntry

    def __init__(self, protected_storage_entry: ProtectedStorageEntry, message_version: int = Version.get_p2p_message_version()):
        super().__init__(message_version)
        self.protected_storage_entry = protected_storage_entry

    # PROTO BUFFER

    @staticmethod
    def from_proto(proto: protobuf.AddDataMessage, resolver: NetworkProtoResolver, message_version: int) -> 'AddDataMessage':
        protected_storage_entry = cast(ProtectedStorageEntry, resolver.from_proto(proto.entry))
        return AddDataMessage(protected_storage_entry, message_version)

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        entry = protobuf.StorageEntryWrapper()
        message: Message = self.protected_storage_entry.to_proto_message()

        if isinstance(self.protected_storage_entry, ProtectedMailboxStorageEntry):
            entry.protected_mailbox_storage_entry = message
        else:
            entry.protected_storage_entry = message
        
        envelope = super().get_network_envelope_builder()
        envelope.add_data_message.CopyFrom(protobuf.AddDataMessage(entry=entry))

        return envelope
