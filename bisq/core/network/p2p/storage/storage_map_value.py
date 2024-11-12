from dataclasses import dataclass
from bisq.core.common.protocol.persistable.persistable_payload import PersistablePayload
import proto.pb_pb2 as protobuf

@dataclass(frozen=True, kw_only=True)
class StorageMapValue(PersistablePayload):
    """
    Used as value in map
    """
    # That object is saved to disc. We need to take care of changes to not break deserialization.
    sequence_nr: int
    time_stamp: int

    def to_proto_message(self):
        return protobuf.MapValue(sequence_nr=self.sequence_nr, time_stamp=self.time_stamp)

    @staticmethod
    def from_proto(proto: protobuf.MapValue):
        return StorageMapValue(sequence_nr=proto.sequence_nr, time_stamp=proto.time_stamp)