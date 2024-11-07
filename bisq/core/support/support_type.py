from enum import IntEnum
from bisq.core.common.protocol.proto_util import ProtoUtil
import proto.pb_pb2 as protobuf

class SupportType(IntEnum):
    ARBITRATION = 0 # Need to be at index 0 to be the fallback for old clients
    MEDIATION = 1
    TRADE = 2
    REFUND = 3

    @staticmethod
    def from_proto(direction: protobuf.SupportType): 
        name = protobuf.SupportType.Name(direction)
        return ProtoUtil.enum_from_proto(SupportType, name)

    @staticmethod
    def to_proto_message(direction: 'SupportType'):
        return protobuf.SupportType.Value(direction.name)
