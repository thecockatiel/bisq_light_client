from enum import IntEnum
from bisq.common.protocol.proto_util import ProtoUtil
import pb_pb2 as protobuf

class SupportType(IntEnum):
    ARBITRATION = 0 # Need to be at index 0 to be the fallback for old clients
    MEDIATION = 1
    TRADE = 2
    REFUND = 3

    @staticmethod
    def from_proto(type: 'protobuf.SupportType'):
        return ProtoUtil.enum_from_proto(SupportType, protobuf.SupportType, type)

    @staticmethod
    def to_proto_message(type: 'SupportType'):
        return ProtoUtil.proto_enum_from_enum(protobuf.SupportType, type)

