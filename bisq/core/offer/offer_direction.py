from enum import Enum, IntEnum
from bisq.core.common.protocol.proto_util import ProtoUtil
import proto.pb_pb2 as protobuf

class OfferDirection(IntEnum):
    BUY = 0
    SELL = 1

    @staticmethod
    def from_proto(direction: protobuf.OfferDirection): 
        name = protobuf.OfferDirection.Name(direction)
        return ProtoUtil.enum_from_proto(OfferDirection, name)

    @staticmethod
    def to_proto_message(direction: 'OfferDirection'):
        return protobuf.OfferDirection.Value(direction.name)
