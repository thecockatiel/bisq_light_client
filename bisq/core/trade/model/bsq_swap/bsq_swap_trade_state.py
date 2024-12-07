
from enum import Enum
from bisq.core.trade.model.trade_phase import TradePhase
from bisq.core.trade.model.trade_state_protocol import TradeStateProtocol
import proto.pb_pb2 as protobuf
from bisq.common.protocol.proto_util import ProtoUtil

class BsqSwapTradeState(TradeStateProtocol, Enum):
    PREPARATION = 0
    COMPLETED = 0
    FAILED = 0
    
    def __init__(self, phase: "TradePhase"):
        self.phase = phase

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
    
    @staticmethod
    def from_proto(proto: protobuf.BsqSwapTrade.State) -> "BsqSwapTradeState":
        return ProtoUtil.enum_from_proto(BsqSwapTradeState, protobuf.BsqSwapTrade.State, proto)

    @staticmethod
    def to_proto_message(state: "BsqSwapTradeState"):
        return ProtoUtil.proto_enum_from_enum(protobuf.BsqSwapTrade.State, state)

