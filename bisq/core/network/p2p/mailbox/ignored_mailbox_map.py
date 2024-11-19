from typing import Dict, Optional
from bisq.common.protocol.persistable.persistable_envelope import PersistableEnvelope
import proto.pb_pb2 as protobuf
from utils.concurrency import ThreadSafeDict

class IgnoredMailboxMap(PersistableEnvelope):
    def __init__(self, ignored: Optional[Dict[str, int]] = None): 
        self.data_map: ThreadSafeDict[str, int] = ThreadSafeDict(ignored if ignored is not None else {})

    def to_proto_message(self) -> protobuf.PersistableEnvelope:
        return protobuf.PersistableEnvelope(
            ignored_mailbox_map=protobuf.IgnoredMailboxMap(data=self.data_map.copy())
        )

    @staticmethod
    def from_proto(proto: protobuf.IgnoredMailboxMap) -> 'IgnoredMailboxMap':
        return IgnoredMailboxMap(proto.data)

    def contains_key(self, uid: str) -> bool:
        return uid in self.data_map
    
    def put(self, uid: str, creation_time_stamp: int) -> None:
        self.data_map.put(uid, creation_time_stamp)

    def __contains__(self, uid: str) -> bool:
        return uid in self.data_map