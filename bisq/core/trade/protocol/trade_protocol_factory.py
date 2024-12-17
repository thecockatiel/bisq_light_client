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
from bisq.core.trade.protocol.trade_protocol import TradeProtocol


# TODO
class TradeProtocolFactory:

    @staticmethod
    def get_new_trade_protocol(trade_model: "TradeModel") -> TradeProtocol:
        raise RuntimeError("get_new_trade_protocol not implemented")
