from dataclasses import dataclass
from google.protobuf.message import Message
import pb_pb2 as protobuf
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload


@dataclass(frozen=True)
class Region(PersistablePayload):
    code: str
    name: str

    @staticmethod
    def from_proto(proto: protobuf.Region) -> "Region":
        return Region(code=proto.code, name=proto.name)

    def to_proto_message(self) -> Message:
        return protobuf.Region(code=self.code, name=self.name)
