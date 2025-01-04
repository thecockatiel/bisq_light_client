from abc import ABC, abstractmethod
from concurrent.futures import Future
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.monetary.price import Price
from bisq.core.monetary.volume import Volume
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.support.dispute.mediation.mediation_result_state import MediationResultState
from bisq.core.support.refund.refund_result_state import RefundResultState
from bisq.core.trade.model.trade_dispute_state import TradeDisputeState
from bisq.core.trade.model.trade_model import TradeModel
from bisq.core.trade.model.trade_period_state import TradePeriodState
from bisq.core.trade.model.trade_phase import TradePhase
from bisq.core.trade.model.trade_state import TradeState
from bisq.core.trade.txproof.asset_tx_proof_result import AssetTxProofResult
from bisq.core.util.volume_util import VolumeUtil
from bitcoinj.base.coin import Coin
from bitcoinj.core.transaction_confidence_type import TransactionConfidenceType
from bisq.common.protocol.proto_util import ProtoUtil
from utils.data import ObservableList, SimpleProperty, SimplePropertyChangeEvent
from utils.time import get_time_ms
import proto.pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.offer.offer import Offer
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.support.messages.chat_messsage import ChatMessage
    from bisq.core.trade.protocol.bisq_v1.model.process_model import ProcessModel
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.trade.model.bisq_v1.contract import Contract
    from bisq.common.crypto.pub_key_ring import PubKeyRing
    from bitcoinj.core.transaction import Transaction
    from bisq.core.protocol.core_proto_resolver import CoreProtoResolver
    from bisq.core.trade.protocol.bisq_v1.model.trading_peer import TradingPeer
    from bisq.core.trade.protocol.provider import Provider
    from bisq.core.trade.protocol.protocol_model import ProtocolModel
    from bitcoinj.core.transaction_confidence import TransactionConfidence


logger = get_logger(__name__)


# NOTE: enums have been moved to their own files prefixed with Trade
# BTC wallet service is removed

# TODO: double check when dependencies were implemented
class Trade(TradeModel, ABC):
    """
    Holds all data which are relevant to the trade, but not those which are only needed in the trade process as shared data between tasks. Those data are
    stored in the task model.
    
    Default constructor makes a "Maker" Trade
    
    To create a "Taker" Trade, use the static method create_taker_trade
    """

    # Maker
    def __init__(
        self,
        *,
        offer: "Offer",
        trade_tx_fee: "Coin",
        taker_fee: "Coin",
        is_currency_for_taker_fee_btc: bool,
        amount: Optional["Coin"] = None, # Taker Trade Specific
        price_as_long: int = 0, # Taker Trade Specific
        trading_peer_node_address: Optional["NodeAddress"] = None, # Taker Trade Specific
        arbitrator_node_address: Optional["NodeAddress"] = None,
        mediator_node_address: Optional["NodeAddress"] = None,
        refund_agent_node_address: Optional["NodeAddress"] = None,
        btc_wallet_service: "BtcWalletService" = None,
        process_model: "ProcessModel"=None,
        uid: str = None,
    ):
        super().__init__(uid, offer)

        # Persistable 
        # Immutable
        self._is_currency_for_taker_fee_btc = is_currency_for_taker_fee_btc
        self._trade_tx_fee_as_long = trade_tx_fee
        self._taker_fee_as_long = taker_fee

        # Mutable
        self._process_model = process_model
        self.taker_fee_tx_id: Optional[str] = None
        self.deposit_tx_id: Optional[str] = None
        self.payout_tx_id: Optional[str] = None
        self.amount_as_long = 0
        self.price_as_long = 0
        # no need for separate state and state_property
        self.state_property = SimpleProperty(TradeState.PREPARATION)
        self.state_phase_property = SimpleProperty(self.state_property.value.phase)
        self.dispute_state_property = SimpleProperty(TradeDisputeState.NO_DISPUTE)
        self.trade_period_state_property = SimpleProperty(TradePeriodState.FIRST_HALF)
        self.contract: Optional["Contract"] = None
        self.contract_as_json: Optional[str] = None
        self.contract_hash: Optional[bytes] = None
        self.taker_contract_signature: Optional[str] = None
        self.maker_contract_signature: Optional[str] = None
        self.arbitrator_node_address = arbitrator_node_address
        self.arbitrator_btc_pub_key: Optional[bytes] = None
        self.arbitrator_pub_key_ring: Optional["PubKeyRing"] = None
        self.mediator_node_address = mediator_node_address
        self.mediator_pub_key_ring: Optional["PubKeyRing"] = None
        self.taker_payment_account_id: Optional[str] = None
        
        self.counter_currency_tx_id: Optional[str] = None
        self._chat_messages = ObservableList["ChatMessage"]()

        # Transient
        # Immutable
        self._trade_tx_fee = trade_tx_fee # is takers tx fee and the tx fee used for all the trade txs. # transient
        self._taker_fee = taker_fee # transient
        self._btc_wallet_service = btc_wallet_service # transient
        
        # Mutable
        self.deposit_tx: Optional["Transaction"] = None # transient
        self.is_initialized = False # transient
        
        # Added in v1.2.0
        self.delayed_payout_tx: Optional["Transaction"] = None # transient
        
        self.payout_tx: Optional["Transaction"] = None # transient
        self.amount_property: SimpleProperty[Optional["Coin"]] = SimpleProperty(None) # transient
        self.volume_property: SimpleProperty[Optional["Volume"]] = SimpleProperty(None) # transient

        # Added in v1.1.6
        self.mediation_result_state_property = SimpleProperty(MediationResultState.UNDEFINED_MEDIATION_RESULT)
        
        # Added in v1.2.0
        self.lock_time = 0
        self.delayed_payout_tx_bytes: Optional[bytes] = None
        self.refund_agent_node_address: Optional["NodeAddress"] = refund_agent_node_address
        self.refund_agent_pub_key_ring: Optional["PubKeyRing"] = None
        self.refund_result_state_property = SimpleProperty(RefundResultState.UNDEFINED_REFUND_RESULT)
    
        # Added at v1.3.8
        # We use that for the XMR txKey but want to keep it generic to be flexible for other payment methods or assets.
        self.counter_currency_extra_data: Optional[str] = None
        
        # Added at v1.3.8
        # Generic tx proof result. We persist name if AssetTxProofResult enum. Other fields in the enum are not persisted
        # as they are not very relevant as historical data (e.g. number of confirmations)
        self.asset_tx_proof_result_property: SimpleProperty[Optional["AssetTxProofResult"]] = SimpleProperty(None)
        
        # Added in v.1.9.13
        self.seller_confirmed_payment_receipt_date = 0
        
        def on_new_state(e: "SimplePropertyChangeEvent[TradeState]"):
            if self.is_initialized:
                # We don't want to log at startup the setState calls from all persisted trades
                logger.info(f"Set new state at {self.__class__.__name__} (id={self.get_short_id()}): {e.new_value}")
                
            if e.new_value.phase.value < e.old_value.phase.value:
                logger.warning(f"We got a state change to a previous phase.\n Old state is: {e.old_value.name}. New state is: {e.new_value.name}")
            self.state_phase_property.set(e.new_value.phase)
            
        self.state_property.add_listener(on_new_state)
        
        # Taker Trade Specific:
        self.price_as_long = price_as_long
        self.trading_peer_node_address = trading_peer_node_address
        if amount:
            self.set_amount(amount)

    @property
    def is_currency_for_taker_fee_btc(self):
        return self._is_currency_for_taker_fee_btc

    @property
    def trade_tx_fee_as_long(self):
        return self._trade_tx_fee_as_long
    
    @property
    def taker_fee_as_long(self):
        return self._taker_fee_as_long
    
    @property
    def process_model(self):
        return self._process_model
    
    @property
    def chat_messages(self):
        return self._chat_messages
    
    @property
    def trade_tx_fee(self):
        return self._trade_tx_fee
    
    @property
    def btc_wallet_service(self):
        return self._btc_wallet_service
    
    @property
    def dispute_state(self):
        return self.dispute_state_property.value
    
    @dispute_state.setter
    def dispute_state(self, dispute_state: "TradeDisputeState"):
        self.dispute_state_property.set(dispute_state)
    
    @property
    def mediation_result_state(self):
        return self.mediation_result_state_property.value
    
    @mediation_result_state.setter
    def mediation_result_state(self, state: "MediationResultState"):
        self.mediation_result_state_property.set(state)
    
    @property
    def refund_result_state(self):
        return self.refund_result_state_property.value
    
    @refund_result_state.setter
    def refund_result_state(self, state: "RefundResultState"):
        self.refund_result_state_property.set(state)
    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self):
        builder = protobuf.Trade(
            offer = self._offer.to_proto_message(),
            is_currency_for_taker_fee_btc = self.is_currency_for_taker_fee_btc,
            tx_fee_as_long = self.trade_tx_fee_as_long,
            taker_fee_as_long = self.taker_fee_as_long,
            take_offer_date = self.take_offer_date,
            process_model = self.process_model.to_proto_message(),
            trade_amount_as_long = self.amount_as_long,
            trade_price = self.price_as_long,
            state = TradeState.to_proto_message(self.state_property.value),
            dispute_state = TradeDisputeState.to_proto_message(self.dispute_state_property.value),
            trade_period_state = TradePeriodState.to_proto_message(self.trade_period_state_property.value),
            chat_message = [msg.to_proto_network_envelope().chat_message for msg in self.chat_messages],
            lock_time = self.lock_time,
            uid = self.uid,
            sellerConfirmedPaymentReceiptDate = self.seller_confirmed_payment_receipt_date, # weird protobuf names
        )
        

        if self.taker_fee_tx_id: builder.taker_fee_tx_id = self.taker_fee_tx_id
        if self.deposit_tx_id: builder.deposit_tx_id = self.deposit_tx_id
        if self.payout_tx_id: builder.payout_tx_id = self.payout_tx_id
        if self.trading_peer_node_address: builder.trading_peer_node_address.CopyFrom(self.trading_peer_node_address.to_proto_message())
        if self.contract: builder.contract.CopyFrom(self.contract.to_proto_message())
        if self.contract_as_json: builder.contract_as_json = self.contract_as_json
        if self.contract_hash: builder.contract_hash = self.contract_hash
        if self.taker_contract_signature: builder.taker_contract_signature = self.taker_contract_signature
        if self.maker_contract_signature: builder.maker_contract_signature = self.maker_contract_signature
        if self.arbitrator_node_address: builder.arbitrator_node_address.CopyFrom(self.arbitrator_node_address.to_proto_message())
        if self.mediator_node_address: builder.mediator_node_address.CopyFrom(self.mediator_node_address.to_proto_message())
        if self.refund_agent_node_address: builder.refund_agent_node_address.CopyFrom(self.refund_agent_node_address.to_proto_message())
        if self.arbitrator_btc_pub_key: builder.arbitrator_btc_pub_key = self.arbitrator_btc_pub_key
        if self.taker_payment_account_id: builder.taker_payment_account_id = self.taker_payment_account_id
        if self.error_message: builder.error_message = self.error_message
        if self.arbitrator_pub_key_ring: builder.arbitrator_pub_key_ring.CopyFrom(self.arbitrator_pub_key_ring.to_proto_message())
        if self.mediator_pub_key_ring: builder.mediator_pub_key_ring.CopyFrom(self.mediator_pub_key_ring.to_proto_message())
        if self.refund_agent_pub_key_ring: builder.refund_agent_pub_key_ring.CopyFrom(self.refund_agent_pub_key_ring.to_proto_message())
        if self.counter_currency_tx_id: builder.counter_currency_tx_id = self.counter_currency_tx_id
        if self.mediation_result_state_property.value: builder.mediation_result_state = MediationResultState.to_proto_message(self.mediation_result_state_property.value)
        if self.refund_result_state_property.value: builder.refund_result_state = RefundResultState.to_proto_message(self.refund_result_state_property.value)
        if self.delayed_payout_tx_bytes: builder.delayed_payout_tx_bytes = self.delayed_payout_tx_bytes
        if self.counter_currency_extra_data: builder.counter_currency_extra_data = self.counter_currency_extra_data
        if self.asset_tx_proof_result_property.value: builder.asset_tx_proof_result = self.asset_tx_proof_result_property.value.name

        return builder

    @staticmethod
    def from_proto(trade: "Trade", proto: "protobuf.Trade", core_proto_resolver: "CoreProtoResolver"):
        trade.take_offer_date = proto.take_offer_date
        trade.state_property.set(TradeState.from_proto(proto.state))
        trade.dispute_state_property.set(TradeDisputeState.from_proto(proto.dispute_state))
        trade.trade_period_state_property.set(TradePeriodState.from_proto(proto.trade_period_state))
        trade.taker_fee_tx_id = ProtoUtil.string_or_none_from_proto(proto.taker_fee_tx_id)
        trade.deposit_tx_id = ProtoUtil.string_or_none_from_proto(proto.deposit_tx_id)
        trade.payout_tx_id = ProtoUtil.string_or_none_from_proto(proto.payout_tx_id)
        trade.contract = Contract.from_proto(proto.contract, core_proto_resolver) if proto.HasField("contract") else None
        trade.contract_as_json = ProtoUtil.string_or_none_from_proto(proto.contract_as_json)
        trade.contract_hash = ProtoUtil.byte_array_or_none_from_proto(proto.contract_hash)
        trade.taker_contract_signature = ProtoUtil.string_or_none_from_proto(proto.taker_contract_signature)
        trade.maker_contract_signature = ProtoUtil.string_or_none_from_proto(proto.maker_contract_signature)
        trade.arbitrator_node_address = NodeAddress.from_proto(proto.arbitrator_node_address) if proto.HasField("arbitrator_node_address") else None
        trade.mediator_node_address = NodeAddress.from_proto(proto.mediator_node_address) if proto.HasField("mediator_node_address") else None
        trade.refund_agent_node_address = NodeAddress.from_proto(proto.refund_agent_node_address) if proto.HasField("refund_agent_node_address") else None
        trade.arbitrator_btc_pub_key = ProtoUtil.byte_array_or_none_from_proto(proto.arbitrator_btc_pub_key)
        trade.taker_payment_account_id = ProtoUtil.string_or_none_from_proto(proto.taker_payment_account_id)
        trade.error_message = ProtoUtil.string_or_none_from_proto(proto.error_message)
        trade.arbitrator_pub_key_ring = PubKeyRing.from_proto(proto.arbitrator_pub_key_ring) if proto.HasField("arbitrator_pub_key_ring") else None
        trade.mediator_pub_key_ring = PubKeyRing.from_proto(proto.mediator_pub_key_ring) if proto.HasField("mediator_pub_key_ring") else None
        trade.refund_agent_pub_key_ring = PubKeyRing.from_proto(proto.refund_agent_pub_key_ring) if proto.HasField("refund_agent_pub_key_ring") else None
        trade.counter_currency_tx_id = proto.counter_currency_tx_id if proto.counter_currency_tx_id else None
        trade.mediation_result_state_property.set(MediationResultState.from_proto(proto.mediation_result_state))
        trade.refund_result_state_property.set(RefundResultState.from_proto(proto.refund_result_state))
        trade.delayed_payout_tx_bytes = ProtoUtil.byte_array_or_none_from_proto(proto.delayed_payout_tx_bytes)
        trade.lock_time = proto.lock_time
        trade.counter_currency_extra_data = ProtoUtil.string_or_none_from_proto(proto.counter_currency_extra_data)

        persisted_asset_tx_proof_result = ProtoUtil.enum_from_proto(AssetTxProofResult, proto.asset_tx_proof_result)
        # We do not want to show the user the last pending state when he starts up the app again, so we clear it.
        if persisted_asset_tx_proof_result == AssetTxProofResult.PENDING:
            persisted_asset_tx_proof_result = None
        trade.asset_tx_proof_result_property.set(persisted_asset_tx_proof_result)

        trade._chat_messages.extend(ChatMessage.from_payload_proto(msg) for msg in proto.chat_message)
        
        trade.seller_confirmed_payment_receipt_date = proto.sellerConfirmedPaymentReceiptDate # weird protobuf names

        return trade

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def initialize(self, service_provider: "Provider"):
        arbitrator = service_provider.arbitrator_manager.get_dispute_agent_by_node_address(self.arbitrator_node_address)
        if arbitrator:
            self.arbitrator_btc_pub_key = arbitrator.btc_pub_key
            self.arbitrator_pub_key_ring = arbitrator.pub_key_ring
            
        mediator = service_provider.mediator_manager.get_dispute_agent_by_node_address(self.mediator_node_address)
        if mediator:
            self.mediator_pub_key_ring = mediator.pub_key_ring
            
        refund_agent = service_provider.refund_agent_manager.get_dispute_agent_by_node_address(self.refund_agent_node_address)
        if refund_agent:
            self.refund_agent_pub_key_ring = refund_agent.pub_key_ring
            
        self.is_initialized = True
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    # The deserialized tx has not actual confidence data, so we need to get the fresh one from the wallet.
    def update_deposit_tx_from_wallet(self):
        if self.get_deposit_tx():
            self.apply_deposit_tx(self.process_model.trade_wallet_service.get_wallet_tx(self.get_deposit_tx().get_tx_id()))
            
    def apply_deposit_tx(self, tx: "Transaction"):
        self.deposit_tx = tx
        self.deposit_tx_id = self.deposit_tx.get_tx_id()
        self.setup_confidence_listener()
        
    def get_deposit_tx(self) -> Optional["Transaction"]:
        if self.deposit_tx is None:
            self.deposit_tx = self.btc_wallet_service.get_transaction(self.deposit_tx_id) if self.deposit_tx_id else None
        return self.deposit_tx
    
    def apply_delayed_payout_tx(self, deplayed_payout_tx: "Transaction"):
        self.delayed_payout_tx = deplayed_payout_tx
        self.delayed_payout_tx_bytes = deplayed_payout_tx.bitcoin_serialize()
    
    def apply_delayed_payout_tx_bytes(self, deplayed_payout_tx_bytes: bytes):
        self.delayed_payout_tx_bytes = deplayed_payout_tx_bytes
    
    # If called from a not initialized trade (or a closed or failed trade)
    # we need to pass the btcWalletService
    def get_delayed_payout_tx(self, btc_wallet_service: Optional["BtcWalletService"] = None) -> Optional["Transaction"]:
        if btc_wallet_service is None:
            btc_wallet_service = self.process_model.btc_wallet_service
        
        if self.delayed_payout_tx is None:
            if btc_wallet_service is None:
                logger.warning("btcWalletService is null. You might call that method before the tradeManager has"
                               "initialized all trades")
                return None

            if self.delayed_payout_tx_bytes is None:
                logger.warning("delayedPayoutTxBytes are null")
                return None
            
            self.delayed_payout_tx = btc_wallet_service.get_tx_from_serialized_tx(self.delayed_payout_tx_bytes)
            
        return self.delayed_payout_tx
    
    def add_and_persist_chat_message(self, chat_message: "ChatMessage"):
        if chat_message not in self._chat_messages:
            self._chat_messages.append(chat_message)
        else:
            logger.error("Trade ChatMessage already exists")
            
    def remove_all_chat_messages(self):
        if len(self._chat_messages) > 0:
            self._chat_messages.clear()
            return True
        return False
    
    @property
    def mediation_result_applied_penalty_to_seller(self) -> bool:
        # If mediated payout is same or more then normal payout we enable otherwise a penalty was applied
        # by mediators and we keep the confirm disabled to avoid that the seller can complete the trade
        # without the penalty.
        payment_amount_from_mediation = self.process_model.seller_payout_amount_from_mediation
        normal_payment_amount = self._offer.seller_security_deposit.value
        return payment_amount_from_mediation < normal_payment_amount
    
    def maybe_clear_sensitive_data(self):
        change = ""
        if self.contract is not None and self.contract.maybe_clear_sensitive_data():
            change += "contract;"
        if self.process_model is not None and self.process_model.maybe_clear_sensitive_data():
            change += "processModel;"
        if self.contract_as_json is not None:
            edited = self.contract.sanitize_contract_as_json(self.contract_as_json)
            if edited != self.contract_as_json:
                change += "contractAsJson;"
        if self.remove_all_chat_messages():
            change += "chat messages;"
        if len(change) > 0:
            logger.info(f"cleared sensitive data from {change} of trade {self.get_short_id()}")

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // TradeModel implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def get_offer(self):
        return self._offer

    def on_complete(self):
        pass
    
    def get_trade_state(self):
        return self.state_property.value
    
    def get_trade_phase(self):
        return self.state_property.value.phase
    
    def get_trade_protocol_model(self) -> "ProtocolModel[TradingPeer]":
        return self._process_model
    
    def is_completed(self):
        return self.is_withdrawn
    
    def get_amount_as_long(self):
        return self.amount_as_long
    
    def get_amount(self) -> "Coin":
        return self.amount_property.value
    
    def get_volume(self) -> "Volume":
        try:
            if self.get_amount() is not None and self.get_price() is not None:
                volume_by_amount = self.get_price().get_volume_by_amount(self.get_amount())
                if self._offer is not None:
                    if self._offer.payment_method.id == PaymentMethod.HAL_CASH_ID:
                        volume_by_amount = VolumeUtil.get_adjusted_volume_for_hal_cash(volume_by_amount)
                    elif self._offer.is_fiat_offer:
                        volume_by_amount = VolumeUtil.get_rounded_fiat_volume(volume_by_amount)
                
                return volume_by_amount
            else:
                return None
        except:
            return None
        
    def get_price(self) -> "Price":
        return Price.value_of(self._offer.currency_code, self.price_as_long)
    
    # getTxFee() is implemented in concrete classes
    # Maker use fee from offer, taker use self.tx_fee

    def get_taker_fee(self) -> "Coin":
        return self._taker_fee
    
    def get_maker_fee(self) -> "Coin":
        return self._offer.maker_fee
    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Abstract
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    @abstractmethod
    def get_payout_amount(self) -> "Coin":
        pass
    
    @abstractmethod
    def confirm_permitted(self) -> bool:
        pass
    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Setters
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def set_state_if_valid_transition_to(self, new_state: "TradeState"):
       if self.state_property.value.is_valid_transition_to(new_state):
           self.state_property.set(new_state)
           return True
       else:
           logger.warning("State change is not getting applied because it would cause an invalid transition. "
                         f"Trade state={self.state_property.value}, intended state={new_state.name}")
           
    def set_amount(self, amount: "Coin"):
        self.amount_property.value = amount
        self.amount_as_long = amount.value
        self.volume_property.value = self.get_volume()
        
    def set_payout_tx(self, payout_tx: "Transaction"):
        self.payout_tx = payout_tx
        self.payout_tx_id = payout_tx.get_tx_id()

    def set_asset_tx_proof_result(self, asset_tx_proof_result: "AssetTxProofResult"):
        self.asset_tx_proof_result_property.value = asset_tx_proof_result
    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getter
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_half_trade_period_date(self) -> datetime:
        return datetime.fromtimestamp((self.get_trade_start_time() + self.get_max_trade_period() / 2) / 1000)

    def get_max_trade_period_date(self) -> datetime:
        return datetime.fromtimestamp((self.get_trade_start_time() + self.get_max_trade_period()) / 1000)

    def get_trade_age(self) -> int:
        return get_time_ms() - self.get_trade_start_time()

    def get_max_trade_period(self) -> int:
        return self._offer.payment_method.max_trade_period

    def get_trade_start_time(self) -> int:
        now = get_time_ms()
        deposit_tx = self.get_deposit_tx()
        start_time = 0
        
        if deposit_tx is not None:
            if deposit_tx.get_confidence().depth > 0:
                trade_time = self.get_date().timestamp() * 1000  # Convert to milliseconds
                # Use included_in_best_chain_at when available, otherwise use update_time
                block_time = (deposit_tx.get_included_in_best_chain_at().timestamp() * 1000 
                            if deposit_tx.get_included_in_best_chain_at() is not None 
                            else deposit_tx.get_update_time().timestamp() * 1000)
                
                # If block date is in future (Date in Bitcoin blocks can be off by +/- 2 hours) we use our current date.
                # If block date is earlier than our trade date we use our trade date.
                if block_time > now:
                    start_time = now
                else:
                    start_time = max(block_time, trade_time)

                logger.debug(f"We set the start for the trade period to {datetime.fromtimestamp(start_time/1000)}. "
                           f"Trade started at: {datetime.fromtimestamp(trade_time/1000)}. "
                           f"Block got mined at: {datetime.fromtimestamp(block_time/1000)}")
            else:
                logger.debug(f"depositTx not confirmed yet. We don't start counting remaining trade period yet. "
                           f"txId={deposit_tx.get_tx_id()}")
                start_time = now
        else:
            start_time = now
            
        return start_time

    @property
    def has_failed(self) -> bool:
        return self.error_message is not None

    @property
    def is_in_preparation(self) -> bool:
        return self.get_trade_phase().value == TradePhase.INIT.value

    @property
    def is_taker_fee_published(self) -> bool:
        return self.get_trade_phase().value >= TradePhase.TAKER_FEE_PUBLISHED.value

    @property
    def is_deposit_published(self) -> bool:
        return self.get_trade_phase().value >= TradePhase.DEPOSIT_PUBLISHED.value

    @property
    def is_funds_locked_in(self) -> bool:
        # If no deposit tx was confirmed we have no funds locked in
        if not self.is_deposit_confirmed:
            return False

        # If we have the payout tx published (non disputed case) we have no funds locked in. Here we might have more
        # complex cases where users open a mediation but continue the trade to finalize it without mediated payout.
        # The trade state handles that but does not handle mediated payouts or refund agents payouts.
        if self.is_payout_published:
            return False

        # Legacy arbitration is not handled anymore as not used anymore.

        # In mediation case we check for the mediationResultState. As there are multiple sub-states we use ordinal.
        if self.dispute_state_property.value == TradeDisputeState.MEDIATION_CLOSED:
            if (self.mediation_result_state_property.value is not None and 
                    self.mediation_result_state_property.value.value >= MediationResultState.PAYOUT_TX_PUBLISHED.value):
                return False

        # In refund agent case the funds are spent anyway with the time locked payout. We do not consider that as
        # locked in funds.
        return (self.dispute_state_property.value != TradeDisputeState.REFUND_REQUESTED and
                self.dispute_state_property.value != TradeDisputeState.REFUND_REQUEST_STARTED_BY_PEER and
                self.dispute_state_property.value != TradeDisputeState.REFUND_REQUEST_CLOSED)

    @property
    def is_deposit_confirmed(self) -> bool:
        return self.get_trade_phase().value >= TradePhase.DEPOSIT_CONFIRMED.value
    
    @property
    def is_fiat_sent(self) -> bool:
        return self.get_trade_phase().value >= TradePhase.FIAT_SENT.value

    @property
    def is_fiat_received(self) -> bool:
        return self.get_trade_phase().value >= TradePhase.FIAT_RECEIVED.value

    @property
    def is_payout_published(self) -> bool:
        return self.get_trade_phase().value >= TradePhase.PAYOUT_PUBLISHED.value or self.is_withdrawn

    @property
    def is_withdrawn(self) -> bool:
        return self.get_trade_phase().value == TradePhase.WITHDRAWN.value

    def get_payout_tx(self) -> "Transaction":
        if self.payout_tx is None:
            self.payout_tx = self.btc_wallet_service.get_transaction(self.payout_tx_id) if self.payout_tx_id else None
        return self.payout_tx

    @property
    def has_error_message(self) -> bool:
        return bool(self.error_message)  # None or empty string will evaluate to False
    
    @property
    def is_tx_chain_invalid(self) -> bool:
        return (self._offer.offer_fee_payment_tx_id is None or
                self.taker_fee_tx_id is None or
                self.deposit_tx_id is None or
                self.get_deposit_tx() is None or
                self.delayed_payout_tx_bytes is None)

    def get_arbitrator_btc_pub_key(self) -> bytes:
        # In case we are already in a trade the arbitrator can have been revoked and we still can complete the trade
        # Only new trades cannot start without any arbitrator
        if self.arbitrator_btc_pub_key is None:
            arbitrator = self.process_model.user.get_accepted_arbitrator_by_address(self.arbitrator_node_address)
            assert arbitrator is not None, "arbitrator must not be None"
            self.arbitrator_btc_pub_key = arbitrator.btc_pub_key
            
        assert self.arbitrator_btc_pub_key is not None, "ArbitratorPubKey must not be None"            
        return self.arbitrator_btc_pub_key

    @property
    def is_bsq_swap(self) -> bool:
        return self._offer is not None and self._offer.is_bsq_swap_offer

    @property
    def is_using_legacy_burning_man(self) -> bool:
        # By checking if burning_man_selection_height is 0 we can detect if the trade was created with
        # the new burningmen receivers or with legacy BM.
        return self.process_model.burning_man_selection_height == 0

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def setup_confidence_listener(self):
        if self.get_deposit_tx() is not None:
            transaction_confidence = self.get_deposit_tx().get_confidence()
            if transaction_confidence.confidence_type == TransactionConfidenceType.BUILDING:
                self.set_confirmed_state()
            else:   
                def on_done(f: Future["TransactionConfidence"]):
                    try:
                        f.result()
                        self.set_confirmed_state()
                    except Exception as e:
                        logger.error(str(e), exc_info=e)
                        raise RuntimeError(e)
                    
                future = transaction_confidence.get_depth_future(1)
                future.add_done_callback(on_done)
        else:
            logger.error("depositTx is None. That must not happen.")

    def set_confirmed_state(self):
        # we only apply the state if we are not already further in the process
        if not self.is_deposit_confirmed:
            # As set_state is called here from the trade itself we cannot trigger a requestPersistence call.
            # But as we get setup_confidence_listener called at startup anyway there is no issue if it would not be
            # persisted in case the shutdown routine did not persist the trade.
            self.state_property.value = TradeState.DEPOSIT_CONFIRMED_IN_BLOCK_CHAIN

    def __str__(self):
        return (f"Trade{{\n"
                f"     offer={self._offer},\n"
                f"     isCurrencyForTakerFeeBtc={self.is_currency_for_taker_fee_btc},\n" 
                f"     tradeTxFeeAsLong={self.trade_tx_fee_as_long},\n"
                f"     takerFeeAsLong={self.taker_fee_as_long},\n"
                f"     takeOfferDate={self.take_offer_date},\n"
                f"     processModel={self.process_model},\n"
                f"     takerFeeTxId='{self.taker_fee_tx_id}',\n"
                f"     depositTxId='{self.deposit_tx_id}',\n"
                f"     payoutTxId='{self.payout_tx_id}',\n"
                f"     tradeAmountAsLong={self.amount_as_long},\n"
                f"     tradePrice={self.price_as_long},\n"
                f"     tradingPeerNodeAddress={self.trading_peer_node_address},\n"
                f"     state={self.state_property.value},\n"
                f"     disputeState={self.dispute_state_property.value},\n"
                f"     tradePeriodState={self.trade_period_state_property.value},\n"
                f"     contract={self.contract},\n"
                f"     contractAsJson='{self.contract_as_json}',\n"
                f"     contractHash={bytes_as_hex_string(self.contract_hash)},\n"
                f"     takerContractSignature='{self.taker_contract_signature}',\n"
                f"     makerContractSignature='{self.maker_contract_signature}',\n"
                f"     arbitratorNodeAddress={self.arbitrator_node_address},\n"
                f"     arbitratorBtcPubKey={bytes_as_hex_string(self.arbitrator_btc_pub_key)},\n"
                f"     arbitratorPubKeyRing={self.arbitrator_pub_key_ring},\n"
                f"     mediatorNodeAddress={self.mediator_node_address},\n"
                f"     mediatorPubKeyRing={self.mediator_pub_key_ring},\n"
                f"     takerPaymentAccountId='{self.taker_payment_account_id}',\n"
                f"     errorMessage='{self.error_message}',\n"
                f"     counterCurrencyTxId='{self.counter_currency_tx_id}',\n"
                f"     counterCurrencyExtraData='{self.counter_currency_extra_data}',\n"
                f"     assetTxProofResult='{self.asset_tx_proof_result_property.value}',\n"
                f"     chatMessages={self.chat_messages},\n"
                f"     tradeTxFee={self.trade_tx_fee},\n"
                f"     takerFee={self._taker_fee},\n"
                f"     btcWalletService={self.btc_wallet_service},\n"
                f"     stateProperty={self.state_property},\n"
                f"     statePhaseProperty={self.state_phase_property},\n"
                f"     disputeStateProperty={self.dispute_state_property},\n"
                f"     tradePeriodStateProperty={self.trade_period_state_property},\n"
                f"     depositTx={self.deposit_tx},\n"
                f"     delayedPayoutTx={self.delayed_payout_tx},\n"
                f"     payoutTx={self.payout_tx},\n"
                f"     tradeAmount={self.get_amount()},\n"
                f"     tradeAmountProperty={self.amount_property},\n"
                f"     tradeVolumeProperty={self.volume_property},\n"
                f"     mediationResultState={self.mediation_result_state_property.value},\n"
                f"     mediationResultStateProperty={self.mediation_result_state_property},\n"
                f"     lockTime={self.lock_time},\n"
                f"     delayedPayoutTxBytes={bytes_as_hex_string(self.delayed_payout_tx_bytes)},\n"
                f"     refundAgentNodeAddress={self.refund_agent_node_address},\n"
                f"     refundAgentPubKeyRing={self.refund_agent_pub_key_ring},\n"
                f"     refundResultState={self.refund_result_state_property.value},\n"
                f"     refundResultStateProperty={self.refund_result_state_property}\n"
                "}")
