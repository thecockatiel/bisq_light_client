from decimal import Decimal
from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.math_utils import MathUtils
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

logger = get_logger(__name__)


class GrpcPriceService(PriceServicer):

    def __init__(self, core_api: "CoreApi", exception_handler: "GrpcExceptionHandler"):
        self.core_api = core_api
        self.exception_handler = exception_handler

    def GetMarketPrice(self, request: "MarketPriceRequest", context: "ServicerContext"):
        try:
            waitable_handler = WaitableResultHandler[float]()
            self.core_api.get_market_price(request.currency_code, waitable_handler)
            price = waitable_handler.wait()
            reply = MarketPriceReply(price=price)
            return reply
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def GetAverageBsqTradePrice(
        self, request: "GetAverageBsqTradePriceRequest", context: "ServicerContext"
    ):
        try:
            prices = self.core_api.get_average_bsq_trade_price(request.days)
            reply = self._build_get_average_bsq_trade_price_reply(prices)
            return reply
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    @staticmethod
    def _build_get_average_bsq_trade_price_reply(
        prices: tuple[Price, Price]
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
