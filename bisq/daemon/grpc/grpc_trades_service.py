from typing import TYPE_CHECKING, Union
from bisq.common.setup.log_setup import get_logger
from bisq.core.api.model.canceled_trade_info import CanceledTradeInfo
from bisq.core.api.model.trade_info import TradeInfo
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.trade.model.bsq_swap.bsq_swap_trade_state import BsqSwapTradeState
from bisq.core.trade.model.trade_model import TradeModel
from bisq.core.trade.model.trade_state import TradeState
from bisq.daemon.grpc.grpc_waitable_callback_handler import GrpcWaitableCallbackHandler
from grpc_pb2_grpc import TradesServicer
from grpc_pb2 import (
    CloseTradeReply,
    CloseTradeRequest,
    ConfirmPaymentReceivedReply,
    ConfirmPaymentReceivedRequest,
    ConfirmPaymentStartedReply,
    ConfirmPaymentStartedRequest,
    ConfirmPaymentStartedXmrRequest,
    FailTradeReply,
    FailTradeRequest,
    GetTradeReply,
    GetTradeRequest,
    GetTradesReply,
    GetTradesRequest,
    TakeOfferRequest,
    TakeOfferReply,
    UnFailTradeReply,
    UnFailTradeRequest,
    WithdrawFundsReply,
    WithdrawFundsRequest,
)
from bisq.core.trade.model.bsq_swap.bsq_swap_trade import BsqSwapTrade

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from grpc import ServicerContext
    from bisq.daemon.grpc.grpc_exception_handler import GrpcExceptionHandler
    from bisq.core.api.core_api import CoreApi

logger = get_logger(__name__)


class GrpcTradesService(TradesServicer):

    def __init__(self, core_api: "CoreApi", exception_handler: "GrpcExceptionHandler"):
        self.core_api = core_api
        self.exception_handler = exception_handler

    def TakeOffer(self, request: "TakeOfferRequest", context: "ServicerContext"):
        try:
            handler = GrpcWaitableCallbackHandler[Union["BsqSwapTrade", "Trade"]]()
            # Make sure the offer exists before trying to take it.
            offer = self.core_api.get_offer(request.offer_id)
            if request.amount == 0:
                intended_trade_amount = offer.amount.value
            else:
                intended_trade_amount = request.amount

            if offer.is_bsq_swap_offer:
                self.core_api.take_bsq_swap_offer(
                    offer.id,
                    intended_trade_amount,
                    handler.handle_result,
                    handler.handle_error_message,
                )
            else:
                self.core_api.take_offer(
                    offer.id,
                    request.payment_account_id,
                    request.taker_fee_currency_code,
                    intended_trade_amount,
                    handler.handle_result,
                    handler.handle_error_message,
                )
            reply = TakeOfferReply()
            trade_model = handler.wait()
            if handler.has_errored:
                logger.error(handler.error_message)
                failure_reason = handler.get_availability_result_with_description()
                reply.failure_reason.CopyFrom(failure_reason)
            else:
                trade_info = None
                if trade_model.get_offer().is_bsq_swap_offer:
                    role = self._get_my_role(trade_model)
                    trade_info = TradeInfo.to_new_trade_info(trade_model, role)
                else:
                    trade_info = TradeInfo.to_new_trade_info(trade_model)
                reply.trade.CopyFrom(trade_info.to_proto_message())
            return reply
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def _get_my_role(self, trade: "TradeModel"):
        return self.core_api.get_trade_role(trade)

    def GetTrade(self, request: "GetTradeRequest", context: "ServicerContext"):
        try:
            trade_model = self.core_api.get_trade_model(request.trade_id)
            was_my_offer = self._was_my_offer(trade_model)
            role = self._get_my_role(trade_model)
            if trade_model.get_offer().is_bsq_swap_offer:
                bsq_swap_trade = self._get_as_bsq_swap_trade(trade_model)
                num_confirmations = self.core_api.get_transaction_confirmations(
                    bsq_swap_trade.tx_id
                )
                if bsq_swap_trade.state == BsqSwapTradeState.COMPLETED:
                    closing_status = self.core_api.get_closed_trade_state_as_string(
                        bsq_swap_trade
                    )
                else:
                    closing_status = "Pending"
                trade_info = TradeInfo.to_trade_info(
                    bsq_swap_trade,
                    role,
                    was_my_offer,
                    closing_status,
                    num_confirmations,
                )
                return GetTradeReply(trade=trade_info.to_proto_message())
            else:
                if trade_model.is_completed():
                    closing_status = self.core_api.get_closed_trade_state_as_string(
                        trade_model
                    )
                else:
                    closing_status = "Pending"
                return GetTradeReply(
                    trade=TradeInfo.to_trade_info(
                        trade_model, role, was_my_offer, closing_status
                    ).to_proto_message()
                )

        except IllegalArgumentException as e:
            self.exception_handler.handle_exception_as_warning(
                logger, "GetTrade", e, context
            )
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def _was_my_offer(self, trade_model: "TradeModel") -> bool:
        return self.core_api.is_my_offer(trade_model.get_offer())

    def _get_as_bsq_swap_trade(self, trade_model: "TradeModel") -> "BsqSwapTrade":
        return trade_model

    def GetTrades(self, request: "GetTradesRequest", context: "ServicerContext"):
        try:
            category = request.category
            if category == GetTradesRequest.Category.OPEN:
                trades = self.core_api.get_open_trades()
            else:
                trades = self.core_api.get_trade_history(category)
            reply = self._build_get_trades_reply(trades, category)
            return reply
        except IllegalArgumentException as e:
            self.exception_handler.handle_exception_as_warning(
                logger, "GetTrades", e, context
            )
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def _build_get_trades_reply(
        self, trades: list["TradeModel"], category: "GetTradesRequest.Category"
    ) -> "GetTradesReply":
        # Build an unsorted List[TradeInfo], starting with
        # all pending, or all completed BsqSwap and v1 trades.
        unsorted_trades: list["TradeInfo"] = []
        for trade_model in trades:
            role = self.core_api.get_trade_role(trade_model)
            is_my_offer = self.core_api.is_my_offer(trade_model.get_offer())
            is_bsq_swap_trade = isinstance(trade_model, BsqSwapTrade)
            num_confirmations = (
                self.core_api.get_transaction_confirmations(trade_model.tx_id)
                if is_bsq_swap_trade
                else 0
            )
            closing_status = (
                "Pending"
                if category == GetTradesRequest.Category.OPEN
                else self.core_api.get_closed_trade_state_as_string(trade_model)
            )
            trade_info = TradeInfo.to_trade_info(
                trade_model, role, is_my_offer, closing_status, num_confirmations
            )
            unsorted_trades.append(trade_info)

        # If closed trades were requested, add any canceled
        # OpenOffers (canceled trades) to the unsorted List[TradeInfo].
        if category == GetTradesRequest.Category.CLOSED:
            canceled_open_offers = self.core_api.get_canceled_open_offers()
            canceled_trades = [
                CanceledTradeInfo.to_canceled_trade_info(open_offer)
                for open_offer in canceled_open_offers
            ]
            unsorted_trades.extend(canceled_trades)

        # Sort the cumulative List<TradeInfo> by date before sending it to the client.
        sorted_trades: list["TradeInfo"] = sorted(unsorted_trades, key=lambda t: t.date)
        return GetTradesReply(
            trades=[trade_info.to_proto_message() for trade_info in sorted_trades]
        )

    def ConfirmPaymentStarted(
        self, request: "ConfirmPaymentStartedRequest", context: "ServicerContext"
    ):
        try:
            self.core_api.confirm_payment_started(request.trade_id)
            return ConfirmPaymentStartedReply()
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def ConfirmPaymentStartedXmr(
        self, request: "ConfirmPaymentStartedXmrRequest", context: "ServicerContext"
    ):
        try:
            self.core_api.confirm_payment_started(
                request.trade_id, request.tx_id, request.tx_key
            )
            return ConfirmPaymentStartedReply()
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def ConfirmPaymentReceived(
        self, request: "ConfirmPaymentReceivedRequest", context: "ServicerContext"
    ):
        try:
            self.core_api.confirm_payment_received(request.trade_id)
            return ConfirmPaymentReceivedReply()
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def CloseTrade(self, request: "CloseTradeRequest", context: "ServicerContext"):
        try:
            self.core_api.close_trade(request.trade_id)
            return CloseTradeReply()
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def WithdrawFunds(
        self, request: "WithdrawFundsRequest", context: "ServicerContext"
    ):
        try:
            self.core_api.withdraw_funds(
                request.trade_id, request.address, request.memo
            )
            return WithdrawFundsReply()
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def FailTrade(self, request: "FailTradeRequest", context: "ServicerContext"):
        try:
            self.core_api.fail_trade(request.trade_id)
            return FailTradeReply()
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def UnFailTrade(self, request: "UnFailTradeRequest", context: "ServicerContext"):
        try:
            self.core_api.unfail_trade(request.trade_id)
            return UnFailTradeReply()
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)
