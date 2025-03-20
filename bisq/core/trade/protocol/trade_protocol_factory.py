from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bisq.core.trade.model.bisq_v1.buyer_as_maker_trade import BuyerAsMakerTrade
from bisq.core.trade.model.bisq_v1.buyer_as_taker_trade import BuyerAsTakerTrade
from bisq.core.trade.model.bisq_v1.seller_as_maker_trade import SellerAsMakerTrade
from bisq.core.trade.model.bisq_v1.seller_as_taker_trade import SellerAsTakerTrade
from bisq.core.trade.model.bsq_swap.bsq_swap_buyer_as_maker_trade import (
    BsqSwapBuyerAsMakerTrade,
)
from bisq.core.trade.model.bsq_swap.bsq_swap_buyer_as_taker_trade import (
    BsqSwapBuyerAsTakerTrade,
)
from bisq.core.trade.model.bsq_swap.bsq_swap_seller_as_maker_trade import (
    BsqSwapSellerAsMakerTrade,
)
from bisq.core.trade.model.bsq_swap.bsq_swap_seller_as_taker_trade import (
    BsqSwapSellerAsTakerTrade,
)
from bisq.core.trade.model.trade_model import TradeModel
from bisq.core.trade.protocol.bisq_v1.buyer_as_maker_protocol import (
    BuyerAsMakerProtocol,
)
from bisq.core.trade.protocol.bisq_v1.buyer_as_taker_protocol import (
    BuyerAsTakerProtocol,
)
from bisq.core.trade.protocol.bisq_v1.seller_as_maker_protocol import (
    SellerAsMakerProtocol,
)
from bisq.core.trade.protocol.bisq_v1.seller_as_taker_protocol import (
    SellerAsTakerProtocol,
)
from bisq.core.trade.protocol.trade_protocol import TradeProtocol


# TODO
class TradeProtocolFactory:

    @staticmethod
    def get_new_trade_protocol(trade_model: "TradeModel") -> TradeProtocol:
        if isinstance(trade_model, BuyerAsMakerTrade):
            return BuyerAsMakerProtocol(trade_model)
        elif isinstance(trade_model, BuyerAsTakerTrade):
            return BuyerAsTakerProtocol(trade_model)
        elif isinstance(trade_model, SellerAsMakerTrade):
            return SellerAsMakerProtocol(trade_model)
        elif isinstance(trade_model, SellerAsTakerTrade):
            return SellerAsTakerProtocol(trade_model)
        elif isinstance(trade_model, BsqSwapBuyerAsMakerTrade):
            raise NotImplementedError(
                "BsqSwapBuyerAsMakerProtocol is not implemented yet"
            )
            # return BsqSwapBuyerAsMakerProtocol(trade_model)
        elif isinstance(trade_model, BsqSwapBuyerAsTakerTrade):
            raise NotImplementedError(
                "BsqSwapBuyerAsTakerProtocol is not implemented yet"
            )
            # return BsqSwapBuyerAsTakerProtocol(trade_model)
        elif isinstance(trade_model, BsqSwapSellerAsMakerTrade):
            raise NotImplementedError(
                "BsqSwapSellerAsMakerProtocol is not implemented yet"
            )
            # return BsqSwapSellerAsMakerProtocol(trade_model)
        elif isinstance(trade_model, BsqSwapSellerAsTakerTrade):
            raise NotImplementedError(
                "BsqSwapSellerAsTakerProtocol is not implemented yet"
            )
            # return BsqSwapSellerAsTakerProtocol(trade_model)
        else:
            raise IllegalStateException(
                f"Trade not of expected type. Trade={trade_model}"
            )
