
from enum import Enum
from bisq.core.locale.res import Res
from bisq.common.protocol.proto_util import ProtoUtil
import pb_pb2 as protobuf

class DisputeResultPayoutSuggestion(Enum):
    UNKNOWN = ("shared.na", None)
    BUYER_GETS_TRADE_AMOUNT = ("disputeSummaryWindow.payout.getsTradeAmount", "shared.buyer")
    BUYER_GETS_TRADE_AMOUNT_PLUS_COMPENSATION = ("disputeSummaryWindow.payout.getsCompensation", "shared.buyer")
    BUYER_GETS_TRADE_AMOUNT_MINUS_PENALTY = ("disputeSummaryWindow.payout.getsPenalty", "shared.buyer")
    SELLER_GETS_TRADE_AMOUNT = ("disputeSummaryWindow.payout.getsTradeAmount", "shared.seller")
    SELLER_GETS_TRADE_AMOUNT_PLUS_COMPENSATION = ("disputeSummaryWindow.payout.getsCompensation", "shared.seller")
    SELLER_GETS_TRADE_AMOUNT_MINUS_PENALTY = ("disputeSummaryWindow.payout.getsPenalty", "shared.seller")
    CUSTOM_PAYOUT = ("disputeSummaryWindow.payout.custom", None)

    def __init__(self, suggestion_key: str, buyer_seller_key: str):
        self.suggestion_key = suggestion_key
        self.buyer_seller_key = buyer_seller_key

    def __str__(self):
        if self.buyer_seller_key is None:
            return Res.get(self.suggestion_key)
        else:
            return Res.get(self.suggestion_key, Res.get(self.buyer_seller_key))
    
    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
    
    @staticmethod
    def from_proto(type: 'protobuf.DisputeResult.PayoutSuggestion'):
        if type is None:
            return DisputeResultPayoutSuggestion.CUSTOM_PAYOUT
        return ProtoUtil.enum_from_proto(DisputeResultPayoutSuggestion, protobuf.DisputeResult.PayoutSuggestion, type)
        
    @staticmethod
    def to_proto_message(type: 'DisputeResultPayoutSuggestion'):
        if type is None:
            return protobuf.DisputeResult.PayoutSuggestion.CUSTOM_PAYOUT
        return ProtoUtil.proto_enum_from_enum(protobuf.DisputeResult.PayoutSuggestion, type)