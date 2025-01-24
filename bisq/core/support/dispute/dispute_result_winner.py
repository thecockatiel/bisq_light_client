from enum import IntEnum
from bisq.common.protocol.proto_util import ProtoUtil
import pb_pb2 as protobuf

class DisputeResultWinner(IntEnum):
    BUYER = 0
    SELLER = 1
    
    @staticmethod
    def from_proto(type: 'protobuf.DisputeResult.Winner'):
        return ProtoUtil.enum_from_proto(DisputeResultWinner, protobuf.DisputeResult.Winner, type)
    
    @staticmethod
    def to_proto_message(type: 'DisputeResultWinner'):
        return ProtoUtil.proto_enum_from_enum(protobuf.DisputeResult.Winner, type)
