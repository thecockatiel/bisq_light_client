from bisq.core.common.protocol.persistable.persistable_envelope import PersistableEnvelope
from bisq.core.network.p2p.storage.p2p_data_storage import P2PDataStorage
from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray
from bisq.core.network.p2p.storage.storage_map_value import StorageMapValue
import proto.pb_pb2 as protobuf
from utils.concurrency import ThreadSafeDict

class SequenceNumberMap(PersistableEnvelope):
    """
    This class was not generalized to HashMapPersistable (like we did with #ListPersistable) because
    in protobuffer the map construct can't be anything, so the straightforward mapping was not possible.
    Hence this Persistable class.
    """
    
    def __init__(self, map: dict[StorageByteArray, StorageMapValue] = None):
        self.map: ThreadSafeDict[StorageByteArray, StorageMapValue] = ThreadSafeDict()
        if map:
            self.map.update(map)
    
    def to_proto_message(self):
        return protobuf.PersistableEnvelope(
            sequence_number_map=protobuf.SequenceNumberMap(
                sequence_number_entries=[
                    protobuf.SequenceNumberEntry(
                        bytes=key.to_proto_message(),
                        map_value=value.to_proto_message()
                    ) for key, value in self.map.items()
                ]
            )
        )
    
    @staticmethod
    def from_proto(proto: protobuf.SequenceNumberMap):
        map = {}
        for e in proto.sequence_number_entries:
            key = StorageByteArray.from_proto(e.bytes)
            value = StorageMapValue.from_proto(e.map_value)
            map[key] = value
        return SequenceNumberMap(map)

    def __len__(self):
        return self.map.__len__()
    
    def __contains__(self, key: StorageByteArray):
        return key in self.map
    
    def __getitem__(self, key: StorageByteArray) -> StorageMapValue:
        return self.map[key]
    
    def __setitem__(self, key: StorageByteArray, value: StorageMapValue):
        self.map[key] = value
            
    def __delitem__(self, key: StorageByteArray) -> None:
        del self.map[key]
            
    def __iter__(self):
        return self.map.__iter__()
    