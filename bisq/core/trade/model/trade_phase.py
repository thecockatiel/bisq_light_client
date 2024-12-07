from enum import IntEnum
from bisq.core.trade.model.trade_phase_protocol import TradePhaseProtocol
import proto.pb_pb2 as protobuf
from bisq.common.protocol.proto_util import ProtoUtil

class TradePhase(TradePhaseProtocol, IntEnum):
    INIT = 0
    TAKER_FEE_PUBLISHED = 1
    DEPOSIT_PUBLISHED = 2
    DEPOSIT_CONFIRMED = 3
    FIAT_SENT = 4
    FIAT_RECEIVED = 5
    PAYOUT_PUBLISHED = 6
    WITHDRAWN = 7
    
    @staticmethod
    def from_proto(proto: protobuf.Trade.Phase) -> "TradePhase":
        return ProtoUtil.enum_from_proto(TradePhase, protobuf.Trade.Phase, proto)

    @staticmethod
    def to_proto_message(phase: "TradePhase"):
        return ProtoUtil.proto_enum_from_enum(protobuf.Trade.Phase, phase)
    
    # We allow a phase change only if the phase a future phase (we cannot limit it to next phase as we have cases where
    # we skip a phase as it is only relevant to one role -> states and phases need a redesign ;-( )
    def is_valid_transition_to(self, new_phase: "TradePhase"):
        # self.value is current phase
        return new_phase.value > self.value

