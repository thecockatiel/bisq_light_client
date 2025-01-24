from typing import TYPE_CHECKING, Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.trade.protocol.protocol_model import ProtocolModel
import pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.trade.protocol.bsq_swap.model.bsq_swap_trade_peer import BsqSwapTradePeer
    from bisq.core.trade.protocol.provider import Provider
    from bisq.core.offer.offer import Offer
    from bisq.core.trade.trade_manager import TradeManager
    from bisq.core.trade.protocol.trade_message import TradeMessage
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.btc.raw_transaction_input import RawTransactionInput
    from bitcoinj.core.transaction import Transaction
    from bisq.common.crypto.pub_key_ring import PubKeyRing
    
# Fields marked as transient are only used during protocol execution which are based on directMessages so we do not
# persist them.

class BsqSwapProtocolModel(ProtocolModel["BsqSwapTradePeer"]):
    """
    This is the base model for the trade protocol. It is persisted with the trade (non transient fields).
    It uses the Provider for access to domain services.
    """
    
    def __init__(self, pub_key_ring: "PubKeyRing", trade_peer: "BsqSwapTradePeer" = None):
        super().__init__()
        
        if trade_peer is None:
            trade_peer = BsqSwapTradePeer()
            
        self.pub_key_ring = pub_key_ring
        self.trade_peer = trade_peer
        
        ### fields
        
        self.provider: Optional["Provider"] = None # transient
        self.trade_manager: Optional["TradeManager"] = None #transient
        self.offer: Optional["Offer"] = None # transient
        self.trade_message: Optional["TradeMessage"] = None # transient
        self.temp_trading_peer_node_address: Optional["NodeAddress"] = None # transient
        self.transaction: Optional["Transaction"] = None # transient
        
        self.btc_address: Optional[str] = None
        self.bsq_address: Optional[str] = None
        self.inputs: Optional[list["RawTransactionInput"]] = None
        self.change: int = 0
        self.payout: int = 0
        self.tx: Optional[bytes] = None
        self.tx_fee: int = 0
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def to_proto_message(self) -> "protobuf.BsqSwapProtocolModel":
        builder = protobuf.BsqSwapProtocolModel(
            change=self.change,
            payout=self.payout,
            trade_peer=self.trade_peer.to_proto_message(),
            pub_key_ring=self.pub_key_ring.to_proto_message(),
            tx_fee=self.tx_fee
        )
        
        if self.btc_address:
            builder.btc_address = self.btc_address
        if self.bsq_address:
            builder.bsq_address = self.bsq_address
        if self.inputs:
            builder.inputs.extend(ProtoUtil.collection_to_proto(self.inputs, protobuf.RawTransactionInput))
        if self.tx:
            builder.tx = self.tx
            
        return builder

    @staticmethod
    def from_proto(proto: "protobuf.BsqSwapProtocolModel") -> "BsqSwapProtocolModel":
        model = BsqSwapProtocolModel(
            pub_key_ring=PubKeyRing.from_proto(proto.pub_key_ring),
            trade_peer=BsqSwapTradePeer.from_proto(proto.trade_peer)
        )
        
        model.change = proto.change
        model.payout = proto.payout
        model.btc_address = ProtoUtil.string_or_none_from_proto(proto.btc_address)
        model.bsq_address = ProtoUtil.string_or_none_from_proto(proto.bsq_address)  
        model.inputs = [RawTransactionInput.from_proto(inp) for inp in proto.inputs] if proto.inputs else None
        model.tx = ProtoUtil.byte_array_or_none_from_proto(proto.tx)
        model.tx_fee = proto.tx_fee
        
        return model

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // TradeProtocolModel
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def apply_transient(self, provider, trade_manager, offer):
        self.offer = offer
        self.provider = provider
        self.trade_manager = trade_manager
    
    @property
    def p2p_service(self):
        return self.provider.p2p_service
    
    @property
    def my_node_address(self):
        return self.p2p_service.get_address()   
    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_complete(self):
        pass
    
    def apply_transaction(self, tx: "Transaction"):
        self.transaction = tx
        self.tx = tx.bitcoin_serialize()
        
    def get_transaction(self) -> "Transaction":
        if self.tx is None:
            return None
        if self.transaction is None:
            deserialized_tx = self.bsq_wallet_service.get_tx_from_serialized_tx(self.tx)
            self.transaction = self.bsq_wallet_service.get_transaction(deserialized_tx.get_tx_id())
        return self.transaction
    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Delegates
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    @property
    def bsq_wallet_service(self):
        return self.provider.bsq_wallet_service

    @property
    def btc_wallet_service(self):
        return self.provider.btc_wallet_service

    @property
    def trade_wallet_service(self):
        return self.provider.trade_wallet_service

    @property
    def wallets_manager(self):
        return self.provider.wallets_manager

    @property
    def dao_facade(self):
        return self.provider.dao_facade

    @property
    def key_ring(self):
        return self.provider.key_ring

    @property
    def filter_manager(self):
        return self.provider.filter_manager

    @property
    def open_offer_manager(self):
        return self.provider.open_offer_manager

    @property
    def offer_id(self):
        return self.offer.id

    def __str__(self):
        return (f"BsqSwapProtocolModel("
                f"\n     offer={self.offer},"
                f"\n     trade_message={self.trade_message},"
                f"\n     temp_trading_peer_node_address={self.temp_trading_peer_node_address},"
                f"\n     transaction={self.get_transaction()},"
                f"\n     trade_peer={self.trade_peer},"
                f"\n     pub_key_ring={self.pub_key_ring},"
                f"\n     btc_address='{self.btc_address}',"
                f"\n     bsq_address='{self.bsq_address}',"
                f"\n     inputs={self.inputs},"
                f"\n     change={self.change},"
                f"\n     payout={self.payout},"
                f"\n     tx={bytes_as_hex_string(self.tx)},"
                f"\n     tx_fee={self.tx_fee}"
                f"\n)")