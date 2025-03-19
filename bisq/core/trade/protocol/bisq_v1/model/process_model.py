from typing import TYPE_CHECKING, Optional
from bisq.common.crypto.hash import get_ripemd160_hash
from bisq.common.crypto.pub_key_ring import PubKeyRing
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.btc.raw_transaction_input import RawTransactionInput
from bisq.core.network.message_state import MessageState
from bisq.core.network.p2p.ack_message import AckMessage
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.trade.model.maker_trade import MakerTrade
from bisq.core.trade.protocol.bisq_v1.model.trading_peer import TradingPeer
from bisq.core.trade.protocol.protocol_model import ProtocolModel
from bitcoinj.base.coin import Coin
import pb_pb2 as protobuf
from utils.data import SimpleProperty
from bisq.core.payment.payment_account import PaymentAccount

if TYPE_CHECKING:
    from bisq.core.trade.protocol.trade_message import TradeMessage
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
    from bisq.core.trade.trade_manager import TradeManager
    from bisq.core.offer.offer import Offer
    from bisq.core.trade.protocol.provider import Provider
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.protocol.core_proto_resolver import CoreProtoResolver
    from bitcoinj.core.transaction import Transaction

# Fields marked as transient are only used during protocol execution which are based on directMessages so we do not
# persist them.

# TODO: this class depends on Provider and TradeManager and their dependencies implementations. double check later
class ProcessModel(ProtocolModel[TradingPeer]):
    """
    This is the base model for the trade protocol. It is persisted with the trade (non transient fields).
    It uses the Provider for access to domain services.
    """
    
    @staticmethod
    def hash_of_payment_account_payload(payment_account_payload: "PaymentAccountPayload") -> bytes:
        assert payment_account_payload, "payment_account_payload must not be None"
        return get_ripemd160_hash(payment_account_payload.serialize_for_hash())
    
    def __init__(self, offer_id: str, account_id: str, pub_key_ring: "PubKeyRing", trading_peer: Optional["TradingPeer"] = None) -> None:
        super().__init__()
        
        # If trading_peer was None in persisted data from some error cases we set a new one to not access None
        if trading_peer is None:
            trading_peer = TradingPeer()
            
        # Persistable Immutable
        self.offer_id = offer_id
        self.pub_key_ring = pub_key_ring
        # Was changed at v1.9.2 from immutable to mutable
        self.account_id = account_id
        # Persistable Mutable
        self._trading_peer = trading_peer
        
        # Transient/Immutable (not set in constructor so they are not final, but at init)
        self._provider: "Provider" = None # transient
        self.trade_manager: "TradeManager" = None # transient
        self._offer: "Offer" = None # transient
        
        # Transient/Mutable
        self._take_offer_fee_tx: "Transaction" = None # transient
        self.trade_message: "TradeMessage" = None # transient
        
        # Added in v1.2.0
        self.delayed_payout_tx_signature: Optional[bytes] = None # transient
        self.prepared_delayed_payout_tx: Optional["Transaction"] = None # transient
        
        # Added in v1.4.0
        # MessageState of the last message sent from the seller to the buyer in the take offer process.
        # It is used only in a task which would not be executed after restart, so no need to persist it.
        self.deposit_tx_message_state_property = SimpleProperty(MessageState.UNDEFINED) # transient
        self.deposit_tx: Optional["Transaction"] = None # transient
        
        self.take_offer_fee_tx_id: Optional[str] = None
        self.payout_tx_signature: Optional[bytes] = None
        self.prepared_deposit_tx: Optional[bytes] = None
        self.raw_transaction_inputs: Optional[list["RawTransactionInput"]] = None
        self.change_output_value: int = 0
        self.change_output_address: Optional[str] = None
        self.use_savings_wallet = False
        self.funds_needed_for_trade_as_long: int = 0
        self.my_multi_sig_pub_key: Optional[bytes] = None
        # that is used to store temp. the peers address when we get an incoming message before the message is verified.
        # After successful verified we copy that over to the trade.tradingPeerAddress
        self.temp_trading_peer_node_address: Optional["NodeAddress"] = None
        
        # Added in v.1.1.6
        self.mediated_payout_tx_signature: Optional[bytes] = None
        self.buyer_payout_amount_from_mediation: int = 0
        self.seller_payout_amount_from_mediation: int = 0
        
        # Was added at v1.9.2
        self.payment_account: Optional["PaymentAccount"] = None
        
        # We want to indicate the user the state of the message delivery of the
        # CounterCurrencyTransferStartedMessage. As well we do an automatic re-send in case it was not ACKed yet.
        # To enable that even after restart we persist the state.
        self.payment_started_message_state_property = SimpleProperty(MessageState.UNDEFINED)
        
        # Added in v 1.9.7
        self.burning_man_selection_height: int = 0
        
        
    def apply_transient(self, provider: "Provider", trade_manager: "TradeManager", offer: "Offer"):
        self._provider = provider
        self.trade_manager = trade_manager
        self._offer = offer
        
    def apply_payment_account(self, trade: "Trade"):
        if isinstance(trade, MakerTrade):
            self.payment_account = self.user.get_payment_account(self._offer.maker_payment_account_id)
        else:
            self.payment_account = self.user.get_payment_account(trade.taker_payment_account_id)
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def to_proto_message(self) -> protobuf.ProcessModel:
        builder = protobuf.ProcessModel(
            trading_peer=self._trading_peer.to_proto_message(),
            offer_id=self._offer_id,
            account_id=self.account_id,
            pub_key_ring=self.pub_key_ring.to_proto_message(),
            change_output_value=self.change_output_value,
            use_savings_wallet=self.use_savings_wallet,
            funds_needed_for_trade_as_long=self.funds_needed_for_trade_as_long,
            payment_started_message_state=self.payment_started_message_state_property.value.name,
            buyer_payout_amount_from_mediation=self.buyer_payout_amount_from_mediation,
            seller_payout_amount_from_mediation=self.seller_payout_amount_from_mediation,
            burning_man_selection_height=self.burning_man_selection_height,
        )
        
        if self.take_offer_fee_tx_id:
            builder.take_offer_fee_tx_id = self.take_offer_fee_tx_id
        if self.payout_tx_signature:
            builder.payout_tx_signature = self.payout_tx_signature
        if self.prepared_deposit_tx:
            builder.prepared_deposit_tx = self.prepared_deposit_tx
        if self.raw_transaction_inputs:
            builder.raw_transaction_inputs.extend(ProtoUtil.collection_to_proto(self.raw_transaction_inputs, protobuf.RawTransactionInput))
        if self.change_output_address:
            builder.change_output_address = self.change_output_address
        if self.my_multi_sig_pub_key:
            builder.my_multi_sig_pub_key = self.my_multi_sig_pub_key
        if self.temp_trading_peer_node_address:
            builder.temp_trading_peer_node_address.CopyFrom(
                self.temp_trading_peer_node_address.to_proto_message()
            )
        if self.mediated_payout_tx_signature:
            builder.mediated_payout_tx_signature = self.mediated_payout_tx_signature
        if self.payment_account:
            builder.payment_account.CopyFrom(self.payment_account.to_proto_message())

        return builder
    
    @staticmethod
    def from_proto(proto: "protobuf.ProcessModel", core_proto_resolver: "CoreProtoResolver") -> "ProcessModel":
        trading_peer = TradingPeer.from_proto(proto.trading_peer, core_proto_resolver)
        pub_key_ring = PubKeyRing.from_proto(proto.pub_key_ring)
        process_model = ProcessModel(proto.offer_id, proto.account_id, pub_key_ring, trading_peer)
        
        process_model.change_output_value = proto.change_output_value
        process_model.use_savings_wallet = proto.use_savings_wallet
        process_model.funds_needed_for_trade_as_long = proto.funds_needed_for_trade_as_long
        process_model.buyer_payout_amount_from_mediation = proto.buyer_payout_amount_from_mediation
        process_model.seller_payout_amount_from_mediation = proto.seller_payout_amount_from_mediation

        # nullable
        process_model.take_offer_fee_tx_id = ProtoUtil.string_or_none_from_proto(proto.take_offer_fee_tx_id)
        process_model.payout_tx_signature = ProtoUtil.byte_array_or_none_from_proto(proto.payout_tx_signature)
        process_model.prepared_deposit_tx = ProtoUtil.byte_array_or_none_from_proto(proto.prepared_deposit_tx)
        
        raw_transaction_inputs = [RawTransactionInput.from_proto(input) for input in proto.raw_transaction_inputs] if proto.raw_transaction_inputs else None
        process_model.raw_transaction_inputs = raw_transaction_inputs
        
        process_model.change_output_address = ProtoUtil.string_or_none_from_proto(proto.change_output_address)
        process_model.my_multi_sig_pub_key = ProtoUtil.byte_array_or_none_from_proto(proto.my_multi_sig_pub_key)
        process_model.temp_trading_peer_node_address = NodeAddress.from_proto(proto.temp_trading_peer_node_address) if proto.HasField('temp_trading_peer_node_address') else None
        process_model.mediated_payout_tx_signature = ProtoUtil.byte_array_or_none_from_proto(proto.mediated_payout_tx_signature)

        payment_started_message_state = MessageState.from_string(ProtoUtil.string_or_none_from_proto(proto.payment_started_message_state))
        process_model.set_payment_started_message_state(payment_started_message_state)
        
        process_model.burning_man_selection_height = proto.burning_man_selection_height

        if proto.HasField('payment_account'):
            process_model.payment_account = PaymentAccount.from_proto(proto.payment_account, core_proto_resolver)

        return process_model

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def on_complete(self):
        pass
    
    @property
    def trade_peer(self):
        return self._trading_peer
    
    @trade_peer.setter
    def trade_peer(self, value: "TradingPeer"):
        self._trading_peer = value
    
    @property
    def take_offer_fee_tx(self):
        return self._take_offer_fee_tx
    
    @take_offer_fee_tx.setter
    def take_offer_fee_tx(self, value: "Transaction"):
        self._take_offer_fee_tx = value
        self.take_offer_fee_tx_id = value.get_tx_id()
    
    def get_payment_account_payload(self, trade: "Trade"):
        if self.payment_account is None:
            # Persisted trades pre v 1.9.2 have no paymentAccount set, so it will be null.
            # We do not need to persist it (though it would not hurt as well).
            self.apply_payment_account(trade)
            
        return self.payment_account.payment_account_payload
    
    def get_funds_needed_for_trade(self):
        return Coin.value_of(self.funds_needed_for_trade_as_long)
    
    def resolve_take_offer_fee_tx(self, trade: "Trade"):
        if self._take_offer_fee_tx is None:
            if not trade.is_currency_for_taker_fee_btc:
                self._take_offer_fee_tx = self.bsq_wallet_service.get_transaction(self.take_offer_fee_tx_id)
            else:
                self._take_offer_fee_tx = self.btc_wallet_service.get_transaction(self.take_offer_fee_tx_id)
        return self._take_offer_fee_tx
    
    @property
    def my_node_address(self):
        return self.p2p_service.address
    
    def set_payment_started_ack_message(self, ack_message: "AckMessage"):
        message_state = MessageState.ACKNOWLEDGED if ack_message.success else MessageState.FAILED
        self.set_payment_started_message_state(message_state)
        
    def set_payment_started_message_state(self, message_state: "MessageState"):
        self.payment_started_message_state_property.value = message_state
        if self.trade_manager is not None:
            self.trade_manager.request_persistence()
        
    def set_deposit_tx_sent_ack_message(self, ack_message: "AckMessage"):
        message_state = MessageState.ACKNOWLEDGED if ack_message.success else MessageState.FAILED
        self.set_deposit_tx_message_state(message_state)
        
    def set_deposit_tx_message_state(self, message_state: "MessageState"):
        self.deposit_tx_message_state_property.value = message_state
        if self.trade_manager is not None:
            self.trade_manager.request_persistence()
            
    def maybe_clear_sensitive_data(self):
        changed = False
        if (self._trading_peer.payment_account_payload is not None or self._trading_peer.contract_as_json is not None):
            # If tradingPeer was null in persisted data from some error cases we set a new one to not cause nullPointers
            self._trading_peer = TradingPeer()
            changed = True
        return changed
    
    @property
    def btc_wallet_service(self):
        return self._provider.btc_wallet_service
    
    @property
    def account_age_witness_service(self):
        return self._provider.account_age_witness_service

    @property
    def p2p_service(self):
        return self._provider.p2p_service 
    
    @property
    def bsq_wallet_service(self):
        return self._provider.bsq_wallet_service

    @property
    def trade_wallet_service(self):
        return self._provider.trade_wallet_service
    
    @property
    def btc_fee_receiver_service(self):
        return self._provider.btc_fee_receiver_service
    
    @property
    def delayed_payout_tx_receiver_service(self):
        return self._provider.delayed_payout_tx_receiver_service
    
    @property
    def user(self):
        return self._provider.user
    
    @property
    def open_offer_manager(self):
        return self._provider.open_offer_manager
    
    @property
    def referral_id_service(self):
        return self._provider.referral_id_service
    
    @property
    def filter_manager(self):
        return self._provider.filter_manager
    
    @property
    def trade_statistics_manager(self):
        return self._provider.trade_statistics_manager
    
    @property
    def arbitrator_manager(self):
        return self._provider.arbitrator_manager
    
    @property
    def mediator_manager(self):
        return self._provider.mediator_manager
    
    @property
    def refund_agent_manager(self):
        return self._provider.refund_agent_manager
    
    @property
    def key_ring(self):
        return self._provider.key_ring
    
    @property
    def dao_facade(self):
        return self._provider.dao_facade

    @property
    def offer(self):
        return self._offer
