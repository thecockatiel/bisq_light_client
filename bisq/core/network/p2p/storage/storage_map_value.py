from dataclasses import dataclass, field
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
import proto.pb_pb2 as protobuf
from utils.data import raise_required

@dataclass(frozen=True)
class StorageMapValue(PersistablePayload):
    """
    Used as value in map
    """
    # That object is saved to disc. We need to take care of changes to not break deserialization.
    sequence_nr: int = field(default_factory=raise_required)
    time_stamp: int = field(default_factory=raise_required)

    def to_proto_message(self):
        return protobuf.MapValue(sequence_nr=self.sequence_nr, time_stamp=self.time_stamp)

    @staticmethod
    def from_proto(proto: protobuf.MapValue):
        return StorageMapValue(sequence_nr=proto.sequence_nr, time_stamp=proto.time_stamp)