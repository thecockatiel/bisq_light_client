from typing import TYPE_CHECKING, Optional
import uuid
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.trade.model.taker_trade import TakerTrade
import proto.pb_pb2 as protobuf
from bisq.core.trade.model.bisq_v1.buyer_trade import BuyerTrade
from bitcoinj.base.coin import Coin
from bisq.core.trade.protocol.bisq_v1.model.process_model import ProcessModel
from bisq.core.network.p2p.node_address import NodeAddress

if TYPE_CHECKING:
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.offer.offer import Offer
    from bisq.core.protocol.core_proto_resolver import CoreProtoResolver
    from bisq.core.trade.model.tradable import Tradable
    

class BuyerAsTakerTrade(BuyerTrade, TakerTrade):
    def __init__(
            self,
            offer: "Offer",
            amount: "Coin",
            trade_tx_fee: "Coin",
            taker_fee: "Coin",
            is_currency_for_taker_fee_btc: bool,
            price_as_long: int,
            trading_peer_node_address: "NodeAddress",
            arbitrator_node_address: Optional["NodeAddress"],
            mediator_node_address: Optional["NodeAddress"],
            refund_agent_node_address: Optional["NodeAddress"],
            btc_wallet_service: "BtcWalletService",
            process_model: "ProcessModel",
            uid: str,
        ):
        super().__init__(
            offer=offer,
            amount=amount,
            trade_tx_fee=trade_tx_fee,
            taker_fee=taker_fee,
            is_currency_for_taker_fee_btc=is_currency_for_taker_fee_btc,
            price_as_long=price_as_long,
            trading_peer_node_address=trading_peer_node_address,
            arbitrator_node_address=arbitrator_node_address,
            mediator_node_address=mediator_node_address,
            refund_agent_node_address=refund_agent_node_address,
            btc_wallet_service=btc_wallet_service,
            process_model=process_model,
            uid=uid,
        )
        
    def to_proto_message(self):
        return protobuf.Tradable(
            protobuf.BuyerAsTakerTrade(
                trade=super().to_proto_message(),
            )
        )
        
    @staticmethod
    def from_proto(buyer_as_taker_proto: protobuf.BuyerAsTakerTrade, btc_wallet_service: "BtcWalletService", core_proto_resolver: "CoreProtoResolver") -> "Tradable":
        trade_proto = buyer_as_taker_proto.trade
        process_model = ProcessModel.from_proto(trade_proto.process_model, core_proto_resolver)
        uid = ProtoUtil.string_or_none_from_proto(trade_proto.uid)
        if uid is None:
            uid = str(uuid.uuid4())
            
        trade = BuyerAsTakerTrade(
            offer=Offer.from_proto(trade_proto.offer),
            amount=Coin.value_of(trade_proto.trade_amount_as_long),
            trade_tx_fee=Coin.value_of(trade_proto.tx_fee_as_long),
            taker_fee=Coin.value_of(trade_proto.taker_fee_as_long),
            is_currency_for_taker_fee_btc=trade_proto.is_currency_for_taker_fee_btc,
            price_as_long=trade_proto.trade_price,
            trading_peer_node_address=NodeAddress.from_proto(trade_proto.trading_peer_node_address) if trade_proto.HasField('trading_peer_node_address') else None,
            arbitrator_node_address=NodeAddress.from_proto(trade_proto.arbitrator_node_address) if trade_proto.HasField('arbitrator_node_address') else None,
            mediator_node_address=NodeAddress.from_proto(trade_proto.mediator_node_address) if trade_proto.HasField('mediator_node_address') else None, 
            refund_agent_node_address=NodeAddress.from_proto(trade_proto.refund_agent_node_address) if trade_proto.HasField('refund_agent_node_address') else None,
            btc_wallet_service=btc_wallet_service,
            process_model=process_model,
            uid=uid
        )
        
        return super().from_proto(trade, trade_proto, core_proto_resolver)

    # The tx fee the user has paid. Not to be confused to the tradeTxFee which is the takers txFee and used for
    # all trade txs
    def get_tx_fee(self) -> "Coin":
        return self.trade_tx_fee.multiply(3)
