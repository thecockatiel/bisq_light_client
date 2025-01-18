from dataclasses import dataclass, field

from bisq.core.network.p2p.storage.messages.broadcast_message import BroadcastMessage
from bisq.core.network.p2p.storage.payload.protected_storage_entry import (
    ProtectedStorageEntry,
)
import proto.pb_pb2 as protobuf

from typing import TYPE_CHECKING

from utils.data import raise_required

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_proto_resolver import (
        NetworkProtoResolver,
    )


@dataclass
class RemoveDataMessage(BroadcastMessage):
    protected_storage_entry: ProtectedStorageEntry = field(default_factory=raise_required)

    # PROTO BUFFER
    def to_proto_network_envelope(self):
        envelope = self.get_network_envelope_builder()
        envelope.remove_data_message.CopyFrom(
            protobuf.RemoveDataMessage(
                protected_storage_entry=self.protected_storage_entry.to_proto_message()
            )
        )
        return envelope

    @staticmethod
    def from_proto(
        proto: "protobuf.RemoveDataMessage",
        resolver: "NetworkProtoResolver",
        message_version: int,
    ):
        return RemoveDataMessage(
            message_version=message_version,
            protected_storage_entry=ProtectedStorageEntry.from_proto(
                proto.protected_storage_entry, resolver
            ),
        )

    def __hash__(self):
        return hash(self.protected_storage_entry)
