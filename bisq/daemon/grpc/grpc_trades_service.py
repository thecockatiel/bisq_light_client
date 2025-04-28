from typing import TYPE_CHECKING, Union
from bisq.common.setup.log_setup import logger_context
from bisq.core.api.model.canceled_trade_info import CanceledTradeInfo
from bisq.core.api.model.trade_info import TradeInfo
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.trade.model.bsq_swap.bsq_swap_trade_state import BsqSwapTradeState
from bisq.core.trade.model.trade_model import TradeModel
from bisq.core.trade.model.trade_state import TradeState
from bisq.core.user.user_context import UserContext
from bisq.core.user.user_manager import UserManager
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


class GrpcTradesService(TradesServicer):

    def __init__(
        self,
        core_api: "CoreApi",
        exception_handler: "GrpcExceptionHandler",
        user_manager: "UserManager",
    ):
        self._core_api = core_api
        self._exception_handler = exception_handler
        self._user_manager = user_manager

    def TakeOffer(self, request: "TakeOfferRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                handler = GrpcWaitableCallbackHandler[Union["BsqSwapTrade", "Trade"]]()
                # Make sure the offer exists before trying to take it.
                offer = self._core_api.get_offer(user_context, request.offer_id)
                if request.amount == 0:
                    intended_trade_amount = offer.amount.value
                else:
                    intended_trade_amount = request.amount

                if offer.is_bsq_swap_offer:
                    self._core_api.take_bsq_swap_offer(
                        user_context,
                        offer.id,
                        intended_trade_amount,
                        handler.handle_result,
                        handler.handle_error_message,
                    )
                else:
                    self._core_api.take_offer(
                        user_context,
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
                    user_context.logger.error(handler.error_message)
                    failure_reason = handler.get_availability_result_with_description()
                    reply.failure_reason.CopyFrom(failure_reason)
                else:
                    trade_info = None
                    if trade_model.get_offer().is_bsq_swap_offer:
                        role = self._get_my_role(user_context, trade_model)
                        trade_info = TradeInfo.to_new_trade_info(trade_model, role)
                    else:
                        trade_info = TradeInfo.to_new_trade_info(trade_model)
                    reply.trade.CopyFrom(trade_info.to_proto_message())
                return reply
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def _get_my_role(self, user_context: "UserContext", trade: "TradeModel"):
        return self._core_api.get_trade_role(user_context, trade)

    def GetTrade(self, request: "GetTradeRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                trade_model = self._core_api.get_trade_model(user_context, request.trade_id)
                was_my_offer = self._was_my_offer(user_context, trade_model)
                role = self._get_my_role(user_context, trade_model)
                if trade_model.get_offer().is_bsq_swap_offer:
                    bsq_swap_trade = self._get_as_bsq_swap_trade(trade_model)
                    num_confirmations = self._core_api.get_transaction_confirmations(
                        user_context, bsq_swap_trade.tx_id
                    )
                    if bsq_swap_trade.state == BsqSwapTradeState.COMPLETED:
                        closing_status = self._core_api.get_closed_trade_state_as_string(
                            user_context, bsq_swap_trade
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
                        closing_status = self._core_api.get_closed_trade_state_as_string(
                            user_context, trade_model
                        )
                    else:
                        closing_status = "Pending"
                    return GetTradeReply(
                        trade=TradeInfo.to_trade_info(
                            trade_model, role, was_my_offer, closing_status
                        ).to_proto_message()
                    )

        except IllegalArgumentException as e:
            self._exception_handler.handle_exception_as_warning(
                user_context.logger, "GetTrade", e, context
            )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def _was_my_offer(
        self, user_context: "UserContext", trade_model: "TradeModel"
    ) -> bool:
        return self._core_api.is_my_offer(user_context, trade_model.get_offer())

    def _get_as_bsq_swap_trade(self, trade_model: "TradeModel") -> "BsqSwapTrade":
        return trade_model

    def GetTrades(self, request: "GetTradesRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                category = request.category
                if category == GetTradesRequest.Category.OPEN:
                    trades = self._core_api.get_open_trades(user_context)
                else:
                    trades = self._core_api.get_trade_history(user_context, category)
                reply = self._build_get_trades_reply(user_context, trades, category)
                return reply
        except IllegalArgumentException as e:
            self._exception_handler.handle_exception_as_warning(
                user_context.logger, "GetTrades", e, context
            )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def _build_get_trades_reply(
        self,
        user_context: "UserContext",
        trades: list["TradeModel"],
        category: "GetTradesRequest.Category",
    ) -> "GetTradesReply":
        # Build an unsorted List[TradeInfo], starting with
        # all pending, or all completed BsqSwap and v1 trades.
        unsorted_trades: list["TradeInfo"] = []
        for trade_model in trades:
            role = self._core_api.get_trade_role(user_context, trade_model)
            is_my_offer = self._core_api.is_my_offer(
                user_context, trade_model.get_offer()
            )
            is_bsq_swap_trade = isinstance(trade_model, BsqSwapTrade)
            num_confirmations = (
                self._core_api.get_transaction_confirmations(
                    user_context, trade_model.tx_id
                )
                if is_bsq_swap_trade
                else 0
            )
            closing_status = (
                "Pending"
                if category == GetTradesRequest.Category.OPEN
                else self._core_api.get_closed_trade_state_as_string(
                    user_context, trade_model
                )
            )
            trade_info = TradeInfo.to_trade_info(
                trade_model, role, is_my_offer, closing_status, num_confirmations
            )
            unsorted_trades.append(trade_info)

        # If closed trades were requested, add any canceled
        # OpenOffers (canceled trades) to the unsorted List[TradeInfo].
        if category == GetTradesRequest.Category.CLOSED:
            canceled_open_offers = self._core_api.get_canceled_open_offers(user_context)
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
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                self._core_api.confirm_payment_started(user_context, request.trade_id)
                return ConfirmPaymentStartedReply()
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def ConfirmPaymentStartedXmr(
        self, request: "ConfirmPaymentStartedXmrRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                self._core_api.confirm_payment_started(
                    user_context,
                    request.trade_id,
                    request.tx_id,
                    request.tx_key,
                )
                return ConfirmPaymentStartedReply()
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def ConfirmPaymentReceived(
        self, request: "ConfirmPaymentReceivedRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                self._core_api.confirm_payment_received(user_context, request.trade_id)
                return ConfirmPaymentReceivedReply()
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def CloseTrade(self, request: "CloseTradeRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                self._core_api.close_trade(user_context, request.trade_id)
                return CloseTradeReply()
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def WithdrawFunds(
        self, request: "WithdrawFundsRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                self._core_api.withdraw_funds(
                    user_context,
                    request.trade_id,
                    request.address,
                    request.memo,
                )
            return WithdrawFundsReply()
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def FailTrade(self, request: "FailTradeRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                self._core_api.fail_trade(user_context, request.trade_id)
                return FailTradeReply()
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def UnFailTrade(self, request: "UnFailTradeRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                self._core_api.unfail_trade(user_context, request.trade_id)
                return UnFailTradeReply()
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)
