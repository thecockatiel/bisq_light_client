
# extracted from P2PDataStorage into its own file
from dataclasses import dataclass, field
from bisq.common.exclude_for_hash_aware_proto import ExcludeForHashAwareProto
from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.core.network.p2p.storage.payload.protected_storage_payload import ProtectedStoragePayload, wrap_in_storage_payload
import pb_pb2 as protobuf
from utils.data import raise_required


@dataclass(frozen=True)
class DataAndSeqNrPair(NetworkPayload, ExcludeForHashAwareProto):
    """
    Used as container for calculating cryptographic hash of data and sequenceNumber.
    """
    # data are only used for calculating cryptographic hash from both values
    protected_storage_payload: ProtectedStoragePayload = field(default_factory=raise_required)
    sequence_number: int = field(default_factory=raise_required)

    def to_proto(self, serialize_for_hash: bool):
        return protobuf.DataAndSeqNrPair(
            payload=self.to_storage_payload_proto(serialize_for_hash),
            sequence_number=self.sequence_number,
        )

    def to_storage_payload_proto(self, serialize_for_hash: bool):
        if isinstance(self.protected_storage_payload, ExcludeForHashAwareProto):
            storage_payload = self.protected_storage_payload.to_proto(serialize_for_hash) # only Filter comes here ??
            return storage_payload
        else:
            return wrap_in_storage_payload(self.protected_storage_payload.to_proto_message())