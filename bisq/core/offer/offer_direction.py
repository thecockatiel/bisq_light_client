from enum import IntEnum
from bisq.common.protocol.proto_util import ProtoUtil
import proto.pb_pb2 as protobuf

class OfferDirection(IntEnum):
    BUY = 0
    SELL = 1

    @staticmethod
    def from_proto(direction: protobuf.OfferDirection):
        return ProtoUtil.enum_from_proto(OfferDirection, protobuf.OfferDirection, direction)

    @staticmethod
    def to_proto_message(direction: 'OfferDirection'):
        return ProtoUtil.proto_enum_from_enum(protobuf.OfferDirection, direction)
