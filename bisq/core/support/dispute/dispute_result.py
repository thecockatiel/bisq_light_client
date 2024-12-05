from typing import TYPE_CHECKING, Optional
from datetime import datetime
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.locale.res import Res
from bisq.core.support.dispute.dispute_result_payout_suggestion import DisputeResultPayoutSuggestion
from bisq.core.support.dispute.dispute_result_reason import DisputeResultReason
from bisq.core.support.dispute.dispute_result_winner import DisputeResultWinner
import proto.pb_pb2 as protobuf
from bisq.common.protocol.network.network_payload import NetworkPayload
from utils.data import SimpleProperty
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.support.messages.chat_messsage import ChatMessage

class DisputeResult(NetworkPayload):
    def __init__(
        self,
        trade_id: str,
        trader_id: int,
        winner: Optional["DisputeResultWinner"] = None,
        reason_ordinal: int = DisputeResultReason.OTHER.value,
        tamper_proof_evidence: bool = False,
        id_verification: bool = False,
        screen_cast: bool = False,
        summary_notes: str = "",
        chat_message: Optional["ChatMessage"] = None,
        arbitrator_signature: Optional[bytes] = None,
        buyer_payout_amount: int = 0,
        seller_payout_amount: int = 0,
        arbitrator_pub_key: Optional[bytes] = None,
        close_date: int = None,
        is_loser_publisher: bool = False,
        payout_adjustment_percent: str = "",
        payout_suggestion: DisputeResultPayoutSuggestion = DisputeResultPayoutSuggestion.CUSTOM_PAYOUT
    ):
        self.trade_id = trade_id
        self.trader_id = trader_id
        self.winner = winner
        self.reason_ordinal = reason_ordinal
        self.tamper_proof_evidence_property = SimpleProperty(tamper_proof_evidence)
        self.id_verification_property = SimpleProperty(id_verification)
        self.screen_cast_property = SimpleProperty(screen_cast)
        self.summary_notes_property = SimpleProperty(summary_notes)
        self.chat_message = chat_message
        self.arbitrator_signature = arbitrator_signature
        self.buyer_payout_amount = buyer_payout_amount
        self.seller_payout_amount = seller_payout_amount
        self.arbitrator_pub_key = arbitrator_pub_key
        self.close_date = close_date if close_date is not None else get_time_ms()
        self.is_loser_publisher = is_loser_publisher
        self.payout_adjustment_percent = payout_adjustment_percent
        self.payout_suggestion = payout_suggestion

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
            tamper_proof_evidence=self.tamper_proof_evidence_property.value,
            id_verification=self.id_verification_property.value,
            screen_cast=self.screen_cast_property.value,
            summary_notes=self.summary_notes_property.value,
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
            f"  tamper_proof_evidence={self.tamper_proof_evidence_property},\n"
            f"  id_verification={self.id_verification_property},\n"
            f"  screen_cast={self.screen_cast_property},\n"
            f"  summary_notes='{self.summary_notes_property}',\n"
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