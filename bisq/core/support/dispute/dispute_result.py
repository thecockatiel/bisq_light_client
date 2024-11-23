from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, Optional
from datetime import datetime
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.common.util.utilities import bytes_as_hex_string
import proto.pb_pb2 as protobuf
from bisq.common.protocol.network.network_payload import NetworkPayload
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.support.messages.chat_messsage import ChatMessage

class Winner(IntEnum):
    BUYER = 0
    SELLER = 1
    
    @staticmethod
    def from_proto(type: 'protobuf.DisputeResult.Winner'):
        return ProtoUtil.enum_from_proto(Winner, protobuf.DisputeResult.Winner, type)
    
    @staticmethod
    def to_proto_message(type: 'Winner'):
        return ProtoUtil.proto_enum_from_enum(protobuf.DisputeResult.Winner, type)


class Reason(IntEnum):
    OTHER = 0
    BUG = 1
    USABILITY = 2
    SCAM = 3                # Not used anymore
    PROTOCOL_VIOLATION = 4  # Not used anymore
    NO_REPLY = 5            # Not used anymore
    BANK_PROBLEMS = 6
    OPTION_TRADE = 7
    SELLER_NOT_RESPONDING = 8
    WRONG_SENDER_ACCOUNT = 9
    TRADE_ALREADY_SETTLED = 10
    PEER_WAS_LATE = 11

    
class PayoutSuggestion(Enum):
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
        # TODO:  not implemented
        return str(self.suggestion_key) + "\t" + str(self.buyer_seller_key)
    
    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
    
    @staticmethod
    def from_proto(type: 'protobuf.DisputeResult.PayoutSuggestion'):
        if type is None:
            return PayoutSuggestion.CUSTOM_PAYOUT
        return ProtoUtil.enum_from_proto(PayoutSuggestion, protobuf.DisputeResult.PayoutSuggestion, type)
        
    @staticmethod
    def to_proto_message(type: 'PayoutSuggestion'):
        if type is None:
            return protobuf.DisputeResult.PayoutSuggestion.CUSTOM_PAYOUT
        return ProtoUtil.proto_enum_from_enum(protobuf.DisputeResult.PayoutSuggestion, type)

@dataclass
class DisputeResult(NetworkPayload):
    trade_id: str
    trader_id: int
    winner: Optional[Winner] = field(default=None)
    reason_ordinal: int = field(default=Reason.OTHER.value)
    tamper_proof_evidence: bool = field(default=False)
    id_verification: bool = field(default=False)
    screen_cast: bool = field(default=False)
    summary_notes: str = field(default="")
    chat_message: Optional["ChatMessage"] = field(default=None)
    arbitrator_signature: Optional[bytes] = field(default=None)
    buyer_payout_amount: int = field(default=0)
    seller_payout_amount: int = field(default=0)
    arbitrator_pub_key: Optional[bytes] = field(default=None)
    close_date: int = field(default_factory=get_time_ms)
    is_loser_publisher: bool = field(default=False)
    payout_adjustment_percent: str = field(default="")
    payout_suggestion: PayoutSuggestion = field(default=PayoutSuggestion.CUSTOM_PAYOUT)
    
    def from_proto(self, proto: protobuf.DisputeResult):
        from bisq.core.support.messages.chat_messsage import ChatMessage
        return DisputeResult(
            trade_id=proto.trade_id,
            trader_id=proto.trader_id,
            winner=Winner.from_proto(proto.winner),
            reason_ordinal=proto.reason_ordinal,
            tamper_proof_evidence=proto.tamper_proof_evidence,
            id_verification=proto.id_verification,
            screen_cast=proto.screen_cast,
            summary_notes=proto.summary_notes,
            chat_message=ChatMessage.from_payload_proto(proto.chat_message) if proto.HasField("chat_message") else None,
            arbitrator_signature=proto.arbitrator_signature,
            buyer_payout_amount=proto.buyer_payout_amount,
            seller_payout_amount=proto.seller_payout_amount,
            arbitrator_pub_key=proto.arbitrator_pub_key,
            close_date=proto.close_date,
            is_loser_publisher=proto.is_loser_publisher,
            payout_adjustment_percent=proto.payout_adjustment_percent,
            payout_suggestion=PayoutSuggestion.from_proto(proto.payout_suggestion)
        )
        
    def to_proto_message(self):
        result = protobuf.DisputeResult(
            trade_id=self.trade_id,
            trader_id=self.trader_id,
            reason_ordinal=self.reason_ordinal,
            tamper_proof_evidence=self.tamper_proof_evidence,
            id_verification=self.id_verification,
            screen_cast=self.screen_cast,
            summary_notes=self.summary_notes,
            buyer_payout_amount=self.buyer_payout_amount,
            seller_payout_amount=self.seller_payout_amount,
            close_date=self.close_date,
            is_loser_publisher=self.is_loser_publisher,
            payout_adjustment_percent=self.payout_adjustment_percent,
            arbitrator_signature=self.arbitrator_signature,
            arbitrator_pub_key=self.arbitrator_pub_key,
        )
        if self.winner:
            result.winner = Winner.to_proto_message(self.winner)
        if self.chat_message:
            result.chat_message.CopyFrom(self.chat_message.to_proto_network_envelope().chat_message)
        if self.payout_suggestion:
            result.payout_suggestion = PayoutSuggestion.to_proto_message(self.payout_suggestion)
        return result

    def set_reason(self, reason: Reason):
        self.reason_ordinal = reason.value

    def get_reason(self) -> Reason:
        return Reason(self.reason_ordinal) if self.reason_ordinal < len(Reason) else Reason.OTHER
    
    def get_close_date(self) -> datetime:
        return datetime.fromtimestamp(self.close_date / 1000)
    
    COMPENSATION_SUGGESTIONS = {
        PayoutSuggestion.BUYER_GETS_TRADE_AMOUNT_MINUS_PENALTY,
        PayoutSuggestion.BUYER_GETS_TRADE_AMOUNT_PLUS_COMPENSATION,
        PayoutSuggestion.SELLER_GETS_TRADE_AMOUNT_MINUS_PENALTY,
        PayoutSuggestion.SELLER_GETS_TRADE_AMOUNT_PLUS_COMPENSATION,
    }

    def get_payout_suggestion_text(self) -> str:
        if self.payout_suggestion in self.COMPENSATION_SUGGESTIONS:
            return f"{self.payout_suggestion} {self.payout_adjustment_percent}%"
        return str(self.payout_suggestion)
    
    def get_payout_suggestion_customized_to_buyer_or_seller(self, is_buyer: bool) -> str:
        # TODO: Res.get not implemented yet
        # see github.com/bisq-network/proposals/issues/407
        if is_buyer:
            match self.payout_suggestion:
                case PayoutSuggestion.BUYER_GETS_TRADE_AMOUNT:
                    return "disputeSummaryWindow.result.buyerGetsTradeAmount"
                case PayoutSuggestion.BUYER_GETS_TRADE_AMOUNT_MINUS_PENALTY:
                    return "disputeSummaryWindow.result.buyerGetsTradeAmountMinusPenalty"
                case PayoutSuggestion.BUYER_GETS_TRADE_AMOUNT_PLUS_COMPENSATION:
                    return "disputeSummaryWindow.result.buyerGetsTradeAmountPlusCompensation"
                case PayoutSuggestion.SELLER_GETS_TRADE_AMOUNT:
                    return "disputeSummaryWindow.result.buyerGetsHisDeposit"
                case PayoutSuggestion.SELLER_GETS_TRADE_AMOUNT_MINUS_PENALTY:
                    return "disputeSummaryWindow.result.buyerGetsHisDepositPlusPenaltyFromSeller"
                case PayoutSuggestion.SELLER_GETS_TRADE_AMOUNT_PLUS_COMPENSATION:
                    return "disputeSummaryWindow.result.buyerGetsHisDepositMinusPenalty"
                case PayoutSuggestion.CUSTOM_PAYOUT:
                    return "disputeSummaryWindow.result.customPayout"
        else:
            match self.payout_suggestion:
                case PayoutSuggestion.SELLER_GETS_TRADE_AMOUNT:
                    return "disputeSummaryWindow.result.sellerGetsTradeAmount"
                case PayoutSuggestion.SELLER_GETS_TRADE_AMOUNT_MINUS_PENALTY:
                    return "disputeSummaryWindow.result.sellerGetsTradeAmountMinusPenalty"
                case PayoutSuggestion.SELLER_GETS_TRADE_AMOUNT_PLUS_COMPENSATION:
                    return "disputeSummaryWindow.result.sellerGetsTradeAmountPlusCompensation"
                case PayoutSuggestion.BUYER_GETS_TRADE_AMOUNT:
                    return "disputeSummaryWindow.result.sellerGetsHisDeposit"
                case PayoutSuggestion.BUYER_GETS_TRADE_AMOUNT_MINUS_PENALTY:
                    return "disputeSummaryWindow.result.sellerGetsHisDepositPlusPenaltyFromBuyer"
                case PayoutSuggestion.BUYER_GETS_TRADE_AMOUNT_PLUS_COMPENSATION:
                    return "disputeSummaryWindow.result.sellerGetsHisDepositMinusPenalty"
                case PayoutSuggestion.CUSTOM_PAYOUT:
                    return "disputeSummaryWindow.result.customPayout"
        return "popup.headline.error"

    def __str__(self):
        return (
            f"DisputeResult(\n"
            f"  trade_id='{self.trade_id}',\n"
            f"  trader_id={self.trader_id},\n"
            f"  winner={self.winner},\n"
            f"  reason_ordinal={self.reason_ordinal},\n"
            f"  tamper_proof_evidence={self.tamper_proof_evidence},\n"
            f"  id_verification={self.id_verification},\n"
            f"  screen_cast={self.screen_cast},\n"
            f"  summary_notes='{self.summary_notes}',\n"
            f"  chat_message={self.chat_message},\n"
            f"  arbitrator_signature={bytes_as_hex_string(self.arbitrator_signature)},\n"
            f"  buyer_payout_amount={self.buyer_payout_amount},\n"
            f"  seller_payout_amount={self.seller_payout_amount},\n"
            f"  arbitrator_pub_key={bytes_as_hex_string(self.arbitrator_pub_key)},\n"
            f"  close_date={self.close_date},\n"
            f"  is_loser_publisher={self.is_loser_publisher},\n"
            f"  payout_adjustment_percent='{self.payout_adjustment_percent}',\n"
            f"  payout_suggestion={self.payout_suggestion}\n)"
        )