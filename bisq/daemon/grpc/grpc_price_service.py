from decimal import Decimal
from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import logger_context
from bisq.common.util.utilities import WaitableResultHandler
from bisq.core.monetary.altcoin import Altcoin
from bisq.core.monetary.price import Price
from bitcoinj.base.utils.fiat import Fiat
from grpc_pb2_grpc import PriceServicer
from grpc_pb2 import (
    AverageBsqTradePrice,
    GetAverageBsqTradePriceReply,
    GetAverageBsqTradePriceRequest,
    MarketPriceReply,
    MarketPriceRequest,
)

if TYPE_CHECKING:
    from grpc import ServicerContext
    from bisq.daemon.grpc.grpc_exception_handler import GrpcExceptionHandler
    from bisq.core.api.core_api import CoreApi
    from bisq.core.user.user_manager import UserManager


class GrpcPriceService(PriceServicer):

    def __init__(
        self,
        core_api: "CoreApi",
        exception_handler: "GrpcExceptionHandler",
        user_manager: "UserManager",
    ):
        self._core_api = core_api
        self._exception_handler = exception_handler
        self._user_manager = user_manager

    def GetMarketPrice(self, request: "MarketPriceRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                waitable_handler = WaitableResultHandler[float]()
                self._core_api.get_market_price(
                    user_context,
                    request.currency_code,
                    waitable_handler,
                )
                price = waitable_handler.wait()
                reply = MarketPriceReply(price=price)
                return reply
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def GetAverageBsqTradePrice(
        self, request: "GetAverageBsqTradePriceRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                prices = self._core_api.get_average_bsq_trade_price(
                    user_context,
                    request.days,
                )
                reply = self._build_get_average_bsq_trade_price_reply(prices)
                return reply
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    @staticmethod
    def _build_get_average_bsq_trade_price_reply(
        prices: tuple[Price, Price],
    ) -> "GetAverageBsqTradePriceReply":
        usd_price = Decimal(str(prices[0])).quantize(
            Decimal("1." + "0" * Fiat.SMALLEST_UNIT_EXPONENT), rounding="ROUND_HALF_UP"
        )
        btc_price = Decimal(str(prices[1])).quantize(
            Decimal("1." + "0" * Altcoin.SMALLEST_UNIT_EXPONENT),
            rounding="ROUND_HALF_UP",
        )
        proto = AverageBsqTradePrice(usd_price=str(usd_price), btc_price=str(btc_price))
        return GetAverageBsqTradePriceReply(price=proto)
