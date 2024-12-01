from bisq.common.protocol.persistable.persistable_envelope import PersistableEnvelope
import proto.pb_pb2 as protobuf
from typing import List


class NavigationPath(PersistableEnvelope):
    def __init__(self, path: List[str] = None):
        self.path: List[str] = path if path is not None else []

    def to_proto_message(self):
        builder = protobuf.NavigationPath()
        if self.path:
            builder.path.extend(self.path)
        return protobuf.PersistableEnvelope(navigation_path=builder)

    @staticmethod
    def from_proto(proto: protobuf.NavigationPath) -> 'NavigationPath':
        return NavigationPath(list(proto.path))

