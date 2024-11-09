from dataclasses import dataclass
from bisq.core.common.protocol.persistable.persistable_payload import PersistablePayload
import proto.pb_pb2 as protobuf
from bisq.core.locale.region import Region


@dataclass(frozen=True)
class Country(PersistablePayload):
    code: str
    name: str
    region: "Region"

    def to_proto_message(self):
        return protobuf.Country(
            code=self.code,
            name=self.name,
            region=self.region.to_proto_message(),
        )

    @staticmethod
    def from_proto(proto: protobuf.Country) -> "Country":
        return Country(
            code=proto.code,
            name=proto.name,
            region=Region.from_proto(proto.region),
        )
