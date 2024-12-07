from typing import TYPE_CHECKING, Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.trade.model.bsq_swap.bsq_swap_buyer_trade import BsqSwapBuyerTrade
from bisq.core.trade.model.bsq_swap.bsq_swap_trade_state import BsqSwapTradeState
from bisq.core.trade.model.taker_trade import TakerTrade
from bitcoinj.base.coin import Coin
import uuid
import proto.pb_pb2 as protobuf
from utils.time import get_time_ms
from bisq.core.trade.protocol.bsq_swap.model.bsq_swap_protocol_model import BsqSwapProtocolModel
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.offer.offer import Offer

class BsqSwapBuyerAsTakerTrade(BsqSwapBuyerTrade, TakerTrade):
    def __init__(self, 
                 offer: 'Offer',
                 amount: 'Coin',
                 peer_node_address: 'NodeAddress',
                 tx_fee_per_vbyte: int,
                 maker_fee: int,
                 taker_fee: int,
                 bsq_swap_protocol_model: 'BsqSwapProtocolModel',
                 take_offer_date: Optional[int] = None,
                 state: Optional[BsqSwapTradeState] = None,
                 uid: Optional[str] = None,
                 error_message: Optional[str] = None,
                 tx_id: Optional[str] = None):
        
        super().__init__(
            uid or str(uuid.uuid4()),
            offer,
            amount,
            take_offer_date or get_time_ms(),
            peer_node_address,
            tx_fee_per_vbyte,
            maker_fee,
            taker_fee,
            bsq_swap_protocol_model,
            error_message,
            state or BsqSwapTradeState.PREPARATION,
            tx_id
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def to_proto_message(self):
        return protobuf.Tradable(
            bsq_swap_buyer_as_taker_trade=protobuf.BsqSwapBuyerAsTakerTrade(
                bsq_swap_trade=super().to_proto_message()
            )
        )
    
    @staticmethod
    def from_proto(bsq_swap_trade: protobuf.BsqSwapBuyerAsTakerTrade):
        proto = bsq_swap_trade.bsq_swap_trade
        return BsqSwapBuyerAsTakerTrade(
            offer=Offer.from_proto(proto.offer),
            amount=Coin.value_of(proto.amount),
            take_offer_date=proto.take_offer_date,
            peer_node_address=NodeAddress.from_proto(proto.peer_node_address) if proto.HasField('peer_node_address') else None,
            tx_fee_per_vbyte=proto.mining_fee_per_byte,
            maker_fee=proto.maker_fee,
            taker_fee=proto.taker_fee,
            bsq_swap_protocol_model=BsqSwapProtocolModel.from_proto(proto.bsq_swap_protocol_model),
            state=BsqSwapTradeState.from_proto(proto.state),
            uid=ProtoUtil.string_or_none_from_proto(proto.uid),
            error_message=ProtoUtil.string_or_none_from_proto(proto.error_message),
            tx_id=ProtoUtil.string_or_none_from_proto(proto.tx_id)
        )