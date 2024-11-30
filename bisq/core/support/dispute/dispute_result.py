from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional
from datetime import datetime
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.locale.res import Res
from bisq.core.support.dispute.dispute_result_payout_suggestion import DisputeResultPayoutSuggestion
from bisq.core.support.dispute.dispute_result_reason import DisputeResultReason
from bisq.core.support.dispute.dispute_result_winner import DisputeResultWinner
import proto.pb_pb2 as protobuf
from bisq.common.protocol.network.network_payload import NetworkPayload
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.support.messages.chat_messsage import ChatMessage

@dataclass
class DisputeResult(NetworkPayload):
    trade_id: str
    trader_id: int
    winner: Optional["DisputeResultWinner"] = field(default=None)
    reason_ordinal: int = field(default=DisputeResultReason.OTHER.value)
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
    payout_suggestion: DisputeResultPayoutSuggestion = field(default=DisputeResultPayoutSuggestion.CUSTOM_PAYOUT)
    
    def from_proto(self, proto: protobuf.DisputeResult):
        from bisq.core.support.messages.chat_messsage import ChatMessage
        return DisputeResult(
            trade_id=proto.trade_id,
            trader_id=proto.trader_id,
            winner=DisputeResultWinner.from_proto(proto.winner),
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
            payout_suggestion=DisputeResultPayoutSuggestion.from_proto(proto.payout_suggestion)
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
            result.winner = DisputeResultWinner.to_proto_message(self.winner)
        if self.chat_message:
            result.chat_message.CopyFrom(self.chat_message.to_proto_network_envelope().chat_message)
        if self.payout_suggestion:
            result.payout_suggestion = DisputeResultPayoutSuggestion.to_proto_message(self.payout_suggestion)
        return result

    def set_reason(self, reason: DisputeResultReason):
        self.reason_ordinal = reason.value

    def get_reason(self) -> DisputeResultReason:
        return DisputeResultReason(self.reason_ordinal) if self.reason_ordinal < len(DisputeResultReason) else DisputeResultReason.OTHER
    
    def get_close_date(self) -> datetime:
        return datetime.fromtimestamp(self.close_date / 1000)
    
    COMPENSATION_SUGGESTIONS = {
        DisputeResultPayoutSuggestion.BUYER_GETS_TRADE_AMOUNT_MINUS_PENALTY,
        DisputeResultPayoutSuggestion.BUYER_GETS_TRADE_AMOUNT_PLUS_COMPENSATION,
        DisputeResultPayoutSuggestion.SELLER_GETS_TRADE_AMOUNT_MINUS_PENALTY,
        DisputeResultPayoutSuggestion.SELLER_GETS_TRADE_AMOUNT_PLUS_COMPENSATION,
    }

    def get_payout_suggestion_text(self) -> str:
        if self.payout_suggestion in self.COMPENSATION_SUGGESTIONS:
            return f"{self.payout_suggestion} {self.payout_adjustment_percent}%"
        return str(self.payout_suggestion)
    
    def get_payout_suggestion_customized_to_buyer_or_seller(self, is_buyer: bool) -> str:
        # see github.com/bisq-network/proposals/issues/407
        if is_buyer:
            match self.payout_suggestion:
                case DisputeResultPayoutSuggestion.BUYER_GETS_TRADE_AMOUNT:
                    return Res.get("disputeSummaryWindow.result.buyerGetsTradeAmount")
                case DisputeResultPayoutSuggestion.BUYER_GETS_TRADE_AMOUNT_MINUS_PENALTY:
                    return Res.get("disputeSummaryWindow.result.buyerGetsTradeAmountMinusPenalty")
                case DisputeResultPayoutSuggestion.BUYER_GETS_TRADE_AMOUNT_PLUS_COMPENSATION:
                    return Res.get("disputeSummaryWindow.result.buyerGetsTradeAmountPlusCompensation")
                case DisputeResultPayoutSuggestion.SELLER_GETS_TRADE_AMOUNT:
                    return Res.get("disputeSummaryWindow.result.buyerGetsHisDeposit")
                case DisputeResultPayoutSuggestion.SELLER_GETS_TRADE_AMOUNT_MINUS_PENALTY:
                    return Res.get("disputeSummaryWindow.result.buyerGetsHisDepositPlusPenaltyFromSeller")
                case DisputeResultPayoutSuggestion.SELLER_GETS_TRADE_AMOUNT_PLUS_COMPENSATION:
                    return Res.get("disputeSummaryWindow.result.buyerGetsHisDepositMinusPenalty")
                case DisputeResultPayoutSuggestion.CUSTOM_PAYOUT:
                    return Res.get("disputeSummaryWindow.result.customPayout")
        else:
            match self.payout_suggestion:
                case DisputeResultPayoutSuggestion.SELLER_GETS_TRADE_AMOUNT:
                    return Res.get("disputeSummaryWindow.result.sellerGetsTradeAmount")
                case DisputeResultPayoutSuggestion.SELLER_GETS_TRADE_AMOUNT_MINUS_PENALTY:
                    return Res.get("disputeSummaryWindow.result.sellerGetsTradeAmountMinusPenalty")
                case DisputeResultPayoutSuggestion.SELLER_GETS_TRADE_AMOUNT_PLUS_COMPENSATION:
                    return Res.get("disputeSummaryWindow.result.sellerGetsTradeAmountPlusCompensation")
                case DisputeResultPayoutSuggestion.BUYER_GETS_TRADE_AMOUNT:
                    return Res.get("disputeSummaryWindow.result.sellerGetsHisDeposit")
                case DisputeResultPayoutSuggestion.BUYER_GETS_TRADE_AMOUNT_MINUS_PENALTY:
                    return Res.get("disputeSummaryWindow.result.sellerGetsHisDepositPlusPenaltyFromBuyer")
                case DisputeResultPayoutSuggestion.BUYER_GETS_TRADE_AMOUNT_PLUS_COMPENSATION:
                    return Res.get("disputeSummaryWindow.result.sellerGetsHisDepositMinusPenalty")
                case DisputeResultPayoutSuggestion.CUSTOM_PAYOUT:
                    return Res.get("disputeSummaryWindow.result.customPayout")
        return Res.get("popup.headline.error")

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