from dataclasses import dataclass, field

from bisq.core.network.p2p.storage.messages.broadcast_message import BroadcastMessage
from bisq.core.network.p2p.storage.payload.protected_storage_entry import (
    ProtectedStorageEntry,
)
import proto.pb_pb2 as protobuf

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_proto_resolver import (
        NetworkProtoResolver,
    )


@dataclass(kw_only=True)
class RemoveDataMessage(BroadcastMessage):
    protected_storage_entry: ProtectedStorageEntry

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
