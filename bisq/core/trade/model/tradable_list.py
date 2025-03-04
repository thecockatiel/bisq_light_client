from typing import TYPE_CHECKING, TypeVar
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.common.protocol.protobuffer_exception import ProtobufferException
from bisq.core.offer.open_offer import OpenOffer
from bisq.core.protocol.core_proto_resolver import CoreProtoResolver
from bisq.core.trade.model.bisq_v1.buyer_as_maker_trade import BuyerAsMakerTrade
from bisq.core.trade.model.bisq_v1.buyer_as_taker_trade import BuyerAsTakerTrade
from bisq.core.trade.model.bisq_v1.seller_as_maker_trade import SellerAsMakerTrade
from bisq.core.trade.model.bisq_v1.seller_as_taker_trade import SellerAsTakerTrade
from bisq.core.trade.model.bsq_swap.bsq_swap_buyer_as_maker_trade import BsqSwapBuyerAsMakerTrade
from bisq.core.trade.model.bsq_swap.bsq_swap_buyer_as_taker_trade import BsqSwapBuyerAsTakerTrade
from bisq.core.trade.model.bsq_swap.bsq_swap_seller_as_maker_trade import BsqSwapSellerAsMakerTrade
from bisq.core.trade.model.bsq_swap.bsq_swap_seller_as_taker_trade import BsqSwapSellerAsTakerTrade
import pb_pb2 as protobuf
from bisq.common.protocol.persistable.persistable_list_as_observable import PersistableListAsObservable

if TYPE_CHECKING:
    from bisq.core.trade.model.tradable import Tradable
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService

T = TypeVar(
    "T", bound="Tradable"
)

class TradableList(PersistableListAsObservable[T]):
    
    def to_proto_message(self):
        return protobuf.PersistableEnvelope(
            tradable_list=protobuf.TradableList(
                tradable=ProtoUtil.collection_to_proto(self.list, protobuf.Tradable)
            )
        )

    @staticmethod
    def from_proto(proto: protobuf.TradableList, core_proto_resolver: "CoreProtoResolver", btc_wallet_service: "BtcWalletService") -> "TradableList":
        tradable_list = []
        for tradable in proto.tradable:
            message_type = tradable.WhichOneof("message")
            if message_type == "open_offer":
                tradable_list.append(OpenOffer.from_proto(tradable.open_offer))
            elif message_type == "buyer_as_maker_trade":
                tradable_list.append(BuyerAsMakerTrade.from_proto(tradable.buyer_as_maker_trade, btc_wallet_service, core_proto_resolver))
            elif message_type == "buyer_as_taker_trade":
                tradable_list.append(BuyerAsTakerTrade.from_proto(tradable.buyer_as_taker_trade, btc_wallet_service, core_proto_resolver))
            elif message_type == "seller_as_maker_trade":
                tradable_list.append(SellerAsMakerTrade.from_proto(tradable.seller_as_maker_trade, btc_wallet_service, core_proto_resolver))
            elif message_type == "seller_as_taker_trade":
                tradable_list.append(SellerAsTakerTrade.from_proto(tradable.seller_as_taker_trade, btc_wallet_service, core_proto_resolver))
            elif message_type == "bsq_swap_buyer_as_maker_trade":
                tradable_list.append(BsqSwapBuyerAsMakerTrade.from_proto(tradable.bsq_swap_buyer_as_maker_trade))
            elif message_type == "bsq_swap_buyer_as_taker_trade":
                tradable_list.append(BsqSwapBuyerAsTakerTrade.from_proto(tradable.bsq_swap_buyer_as_taker_trade))
            elif message_type == "bsq_swap_seller_as_maker_trade":
                tradable_list.append(BsqSwapSellerAsMakerTrade.from_proto(tradable.bsq_swap_seller_as_maker_trade))
            elif message_type == "bsq_swap_seller_as_taker_trade":
                tradable_list.append(BsqSwapSellerAsTakerTrade.from_proto(tradable.bsq_swap_seller_as_taker_trade))
            else:
                raise ProtobufferException(f"Unknown messageCase. tradable.WhichOneof('message') = {message_type}")
        
        return TradableList(tradable_list)

    def __str__(self):
        return f"TradableList{{,\n     list={self.list}\n}}"
