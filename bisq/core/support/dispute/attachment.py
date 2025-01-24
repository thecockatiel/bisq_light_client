from dataclasses import dataclass
from bisq.common.protocol.network.network_payload import NetworkPayload
import pb_pb2 as protobuf


@dataclass(frozen=True)
class Attachment(NetworkPayload):
    file_name: str
    bytes: bytes

    def to_proto_message(self) -> protobuf.Attachment:
        return protobuf.Attachment(
            file_name=self.file_name,
            bytes=self.bytes,
        )

    @staticmethod
    def from_proto(proto: protobuf.Attachment) -> "Attachment":
        return Attachment(file_name=proto.file_name, bytes=proto.bytes)

    def __str__(self) -> str:
        return f"Attachment{{file_name='{self.file_name}', bytes={len(self.bytes)}}}"
