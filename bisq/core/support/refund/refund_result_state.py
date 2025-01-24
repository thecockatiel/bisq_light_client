
from enum import IntEnum
from bisq.common.protocol.proto_util import ProtoUtil
import pb_pb2 as protobuf

# JAVA TODO
class RefundResultState(IntEnum):
    UNDEFINED_REFUND_RESULT = 0
    
    @staticmethod
    def from_proto(proto: protobuf.RefundResultState) -> 'RefundResultState':
        return ProtoUtil.enum_from_proto(RefundResultState, protobuf.RefundResultState, proto)
    
    @staticmethod
    def to_proto_message(state: "RefundResultState"):
        return ProtoUtil.proto_enum_from_enum(protobuf.RefundResultState, state)

