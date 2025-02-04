from typing import TYPE_CHECKING
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
import grpc_pb2

if TYPE_CHECKING:
    from bisq.cli.grpc_stubs import GrpcStubs


class TradesServiceRequest:

    def __init__(self, grpc_stubs: "GrpcStubs"):
        self.grpc_stubs = grpc_stubs

    def get_take_offer_reply(
        self,
        offer_id: str,
        payment_account_id: str,
        taker_fee_currency_code: str,
        amount: int,
    ) -> grpc_pb2.TakeOfferReply:
        request = grpc_pb2.TakeOfferRequest(
            offer_id=offer_id,
            payment_account_id=payment_account_id,
            taker_fee_currency_code=taker_fee_currency_code,
            amount=amount,
        )
        response: grpc_pb2.TakeOfferReply = self.grpc_stubs.trades_service.TakeOffer(
            request
        )
        return response

    def take_bsq_swap_offer(self, offer_id: str, amount: int) -> grpc_pb2.TradeInfo:
        reply = self.get_take_offer_reply(
            offer_id=offer_id,
            payment_account_id="",
            taker_fee_currency_code="",
            amount=amount,
        )
        if reply.HasField("trade"):
            return reply.trade
        else:
            raise IllegalStateException(reply.failure_reason.description)

    def take_offer(
        self,
        offer_id: str,
        payment_account_id: str,
        taker_fee_currency_code: str,
        amount: int,
    ) -> grpc_pb2.TradeInfo:
        reply = self.get_take_offer_reply(
            offer_id=offer_id,
            payment_account_id=payment_account_id,
            taker_fee_currency_code=taker_fee_currency_code,
            amount=amount,
        )
        if reply.HasField("trade"):
            return reply.trade
        else:
            raise IllegalStateException(reply.failure_reason.description)

    def get_trade(self, trade_id: str) -> grpc_pb2.TradeInfo:
        request = grpc_pb2.GetTradeRequest(trade_id=trade_id)
        response: grpc_pb2.GetTradeReply = self.grpc_stubs.trades_service.GetTrade(
            request
        )
        return response.trade

    def get_open_trades(self) -> list[grpc_pb2.TradeInfo]:
        request = grpc_pb2.GetTradesRequest()
        response: grpc_pb2.GetTradesReply = self.grpc_stubs.trades_service.GetTrades(
            request
        )
        return response.trades

    def get_trade_history(
        self, category: grpc_pb2.GetTradesRequest.Category
    ) -> list[grpc_pb2.TradeInfo]:
        if category not in (
            grpc_pb2.GetTradesRequest.Category.CLOSED,
            grpc_pb2.GetTradesRequest.Category.FAILED,
        ):
            raise IllegalStateException(
                f"unrecognized gettrades category parameter {ProtoUtil.proto_enum_to_str(grpc_pb2.GetTradesRequest.Category, category)}"
            )

        request = grpc_pb2.GetTradesRequest(category=category)
        response: grpc_pb2.GetTradesReply = self.grpc_stubs.trades_service.GetTrades(
            request
        )
        return response.trades

    def confirm_payment_started(
        self, trade_id: str
    ) -> grpc_pb2.ConfirmPaymentStartedReply:
        request = grpc_pb2.ConfirmPaymentStartedRequest(trade_id=trade_id)
        response: grpc_pb2.ConfirmPaymentStartedReply = (
            self.grpc_stubs.trades_service.ConfirmPaymentStarted(request)
        )
        return response

    def confirm_payment_started_xmr(
        self, trade_id: str, tx_id: str, tx_key: str
    ) -> grpc_pb2.ConfirmPaymentStartedReply:
        request = grpc_pb2.ConfirmPaymentStartedXmrRequest(
            trade_id=trade_id,
            tx_id=tx_id,
            tx_key=tx_key,
        )
        response: grpc_pb2.ConfirmPaymentStartedReply = (
            self.grpc_stubs.trades_service.ConfirmPaymentStartedXmr(request)
        )
        return response

    def confirm_payment_received(
        self, trade_id: str
    ) -> grpc_pb2.ConfirmPaymentReceivedReply:
        request = grpc_pb2.ConfirmPaymentReceivedRequest(trade_id=trade_id)
        response: grpc_pb2.ConfirmPaymentReceivedReply = (
            self.grpc_stubs.trades_service.ConfirmPaymentReceived(request)
        )
        return response

    def close_trade(self, trade_id: str) -> grpc_pb2.CloseTradeReply:
        request = grpc_pb2.CloseTradeRequest(trade_id=trade_id)
        response: grpc_pb2.CloseTradeReply = self.grpc_stubs.trades_service.CloseTrade(
            request
        )
        return response

    def withdraw_funds(
        self, trade_id: str, address: str, memo: str
    ) -> grpc_pb2.WithdrawFundsReply:
        request = grpc_pb2.WithdrawFundsRequest(
            trade_id=trade_id,
            address=address,
            memo=memo,
        )
        response: grpc_pb2.WithdrawFundsReply = (
            self.grpc_stubs.trades_service.WithdrawFunds(request)
        )
        return response

    def fail_trade(self, trade_id: str) -> grpc_pb2.FailTradeReply:
        request = grpc_pb2.FailTradeRequest(trade_id=trade_id)
        response: grpc_pb2.FailTradeReply = self.grpc_stubs.trades_service.FailTrade(
            request
        )
        return response

    def unfail_trade(self, trade_id: str) -> grpc_pb2.UnFailTradeReply:
        request = grpc_pb2.UnFailTradeRequest(trade_id=trade_id)
        response: grpc_pb2.UnFailTradeReply = (
            self.grpc_stubs.trades_service.UnFailTrade(request)
        )
        return response
