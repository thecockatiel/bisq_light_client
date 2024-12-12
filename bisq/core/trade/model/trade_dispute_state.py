from enum import IntEnum
import proto.pb_pb2 as protobuf
from bisq.common.protocol.proto_util import ProtoUtil

class TradeDisputeState(IntEnum):
    NO_DISPUTE = 0
    
    # arbitration
    DISPUTE_REQUESTED = 1
    DISPUTE_STARTED_BY_PEER = 2
    DISPUTE_CLOSED = 3
    
    # mediation
    MEDIATION_REQUESTED = 4
    MEDIATION_STARTED_BY_PEER = 5
    MEDIATION_CLOSED = 6
    
    # refund
    REFUND_REQUESTED = 7
    REFUND_REQUEST_STARTED_BY_PEER = 8
    REFUND_REQUEST_CLOSED = 9
    
    @staticmethod
    def from_proto(proto: protobuf.Trade.DisputeState) -> "TradeDisputeState":
        return ProtoUtil.enum_from_proto(TradeDisputeState, protobuf.Trade.DisputeState, proto)

    @staticmethod
    def to_proto_message(state: "TradeDisputeState"):
        return ProtoUtil.proto_enum_from_enum(protobuf.Trade.DisputeState, state)
    
    @property
    def is_not_disputed(self):
        return self == TradeDisputeState.NO_DISPUTE
    
    @property
    def is_mediated(self):
        return self in [
            TradeDisputeState.MEDIATION_REQUESTED,
            TradeDisputeState.MEDIATION_STARTED_BY_PEER,
            TradeDisputeState.MEDIATION_CLOSED
        ]
    
    @property
    def is_arbitrated(self):
        return self in [
            TradeDisputeState.DISPUTE_REQUESTED,
            TradeDisputeState.DISPUTE_STARTED_BY_PEER,
            TradeDisputeState.DISPUTE_CLOSED,
            TradeDisputeState.REFUND_REQUESTED,
            TradeDisputeState.REFUND_REQUEST_STARTED_BY_PEER,
            TradeDisputeState.REFUND_REQUEST_CLOSED
        ]
