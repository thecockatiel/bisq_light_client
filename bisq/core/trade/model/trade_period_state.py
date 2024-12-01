from enum import IntEnum
import proto.pb_pb2 as protobuf
from bisq.common.protocol.proto_util import ProtoUtil

class TradePeriodState(IntEnum):
    FIRST_HALF = 0
    SECOND_HALF = 1
    TRADE_PERIOD_OVER = 2
    
    @staticmethod
    def from_proto(proto: protobuf.Trade.TradePeriodState) -> "TradePeriodState":
        return ProtoUtil.enum_from_proto(TradePeriodState, protobuf.Trade.TradePeriodState, proto)

    @staticmethod
    def to_proto_message(state: "TradePeriodState"):
        return ProtoUtil.proto_enum_from_enum(protobuf.Trade.TradePeriodState, state)
