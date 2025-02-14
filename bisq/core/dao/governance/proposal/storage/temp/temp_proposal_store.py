from typing import TYPE_CHECKING
from bisq.common.crypto.hash import get_32_byte_hash
from bisq.common.protocol.persistable.persistable_envelope import PersistableEnvelope
from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray
from utils.concurrency import ThreadSafeDict
from bisq.core.network.p2p.storage.payload.protected_storage_entry import (
    ProtectedStorageEntry,
)
import pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver


class TempProposalStore(PersistableEnvelope):
    """
    We store only the payload in the PB file to save disc space. The hash of the payload can be created anyway and
    is only used as key in the map. So we have a hybrid data structure which is represented as list in the protobuffer
    definition and provide a hashMap for the domain access.
    """

    def __init__(self, list_: list["ProtectedStorageEntry"] = None):
        self.map = ThreadSafeDict["StorageByteArray", "ProtectedStorageEntry"]()

        if list_:
            for entry in list_:
                key = StorageByteArray(
                    get_32_byte_hash(entry.protected_storage_payload)
                )
                self.map[key] = entry

    def to_proto_message(self):
        return protobuf.PersistableEnvelope(
            temp_proposal_store=protobuf.TempProposalStore(
                items=[item.to_protected_storage_entry() for item in self.map.values()]
            )
        )

    @staticmethod
    def from_proto(
        proto: protobuf.TempProposalStore,
        network_proto_resolver: "NetworkProtoResolver",
    ):
        list = [
            ProtectedStorageEntry.from_proto(entry, network_proto_resolver)
            for entry in proto.items
        ]
        return TempProposalStore(list)

    def contains_key(self, hash: "StorageByteArray"):
        return hash in self.map
