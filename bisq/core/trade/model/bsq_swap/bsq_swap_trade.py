from bisq.common.setup.log_setup import get_logger
from bisq.core.monetary.price import Price
from bisq.core.monetary.volume import Volume
from bisq.core.offer.offer import Offer
from bisq.core.trade.model.bsq_swap.bsq_swap_calculation import BsqSwapCalculation
from bisq.core.trade.model.bsq_swap.bsq_swap_trade_state import BsqSwapTradeState
from bisq.core.trade.model.trade_model import TradeModel
from bitcoinj.base.coin import Coin
from utils.data import SimpleProperty
from typing import TYPE_CHECKING, Optional
import pb_pb2 as protobuf

if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bisq.core.trade.protocol.bsq_swap.model.bsq_swap_protocol_model import BsqSwapProtocolModel
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService

logger = get_logger(__name__)

class BsqSwapTrade(TradeModel):
    def __init__(self, 
                 uid: str,
                 offer: "Offer",
                 amount: "Coin",
                 take_offer_date: int,
                 trading_peer_node_address: "NodeAddress",
                 tx_fee_per_vbyte: int,
                 maker_fee_as_long: int,
                 taker_fee_as_long: int,
                 bsq_swap_protocol_model: "BsqSwapProtocolModel",
                 error_message: Optional[str],
                 state: "BsqSwapTradeState",
                 tx_id: Optional[str]):
        super().__init__(uid, offer, take_offer_date, trading_peer_node_address, error_message)
        self._amount_as_long = amount.value
        self._tx_fee_per_vbyte = tx_fee_per_vbyte
        self._maker_fee_as_long = maker_fee_as_long
        self._taker_fee_as_long = taker_fee_as_long
        self._bsq_swap_protocol_model = bsq_swap_protocol_model
        self._tx_id = tx_id
        self._state_property = SimpleProperty(state)
        
        self._volume: Optional["Volume"] = None # transient
        self._transaction: Optional["Transaction"] = None # transient

    @property
    def is_bsq_swap(self) -> bool:
        # does not make much sense to have a bsq swap trade without a bsq swap offer
        # but we can't be exactly sure that the offer is a bsq swap offer anyway.
        return self._offer.is_bsq_swap_offer

    @property
    def tx_fee_per_vbyte(self) -> int:
        return self._tx_fee_per_vbyte

    @property
    def taker_fee_as_long(self) -> int:
        return self._taker_fee_as_long
    
    @property
    def maker_fee_as_long(self):
        return self._maker_fee_as_long

    @property
    def bsq_swap_protocol_model(self) -> "BsqSwapProtocolModel":
        return self._bsq_swap_protocol_model

    @property
    def state(self) -> "BsqSwapTradeState":
        return self._state_property.value
    
    @state.setter
    def state(self, state: "BsqSwapTradeState"):
        if state.value < self.state.value:
            logger.warning("Unexpected state change to a previous state.\n"
                           f"Old state is: {self.state.name}. New state is: {state.name}")
        self._state_property.value = state

    @property
    def tx_id(self) -> Optional[str]:
        return self._tx_id

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def toProtoMessage(self):
        builder = protobuf.BsqSwapTrade(
            uid=self.uid,
            offer=self._offer.to_proto_message(),
            amount=self._amount_as_long,
            take_offer_date=self.take_offer_date,
            mining_fee_per_byte=self.tx_fee_per_vbyte,
            maker_fee=self._maker_fee_as_long,
            taker_fee=self._taker_fee_as_long,
            bsq_swap_protocol_model=self.bsq_swap_protocol_model.to_proto_message(),
            state=BsqSwapTradeState.to_proto_message(self.state),
            peer_node_address=self.trading_peer_node_address.to_proto_message()
        )
        
        if self.error_message:
            builder.error_message = self.error_message
        if self.tx_id:
            builder.tx_id = self.tx_id
            
        return builder

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Model implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_complete(self) -> bool:
        pass
    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // TradeModel implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def get_trade_protocol_model(self):
        return self.bsq_swap_protocol_model
    
    def is_completed(self) -> bool:
        return self.state == BsqSwapTradeState.COMPLETED
    
    def get_trade_state(self):
        return self.state
    
    def get_trade_phase(self):
        return self.state.phase
    
    def get_amount_as_long(self):
        return self._amount_as_long
    
    def get_amount(self):
        return Coin.value_of(self._amount_as_long)
    
    def get_volume(self):
        if self._volume is None:
            try:
                self._volume = self.get_price().get_volume_by_amount(Coin.value_of(self._amount_as_long))
            except Exception as e:
                logger.error(repr(e))
                return None
        return self._volume
    
    def get_price(self):
        return Price.value_of(self._offer.currency_code, self._offer.fixed_price)
    
    def get_tx_fee(self):
        return Coin.value_of(self.bsq_swap_protocol_model.tx_fee)
    
    def get_taker_fee(self):
        return Coin.value_of(self._taker_fee_as_long)
    
    def get_maker_fee(self):
        return Coin.value_of(self._maker_fee_as_long)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Setters
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def apply_transaction(self, transaction: "Transaction"):
        self._transaction = transaction
        self.tx_id = transaction.get_tx_id()
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getters
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    @property
    def has_failed(self):
        return self.error_message is not None
    
    def get_bsq_trade_amount(self):
        volume = self.get_volume()
        if volume is None:
            return 0
        return BsqSwapCalculation.get_bsq_trade_amount(volume).value
    
    def get_transaction(self, bsq_wallet_service: "BsqWalletService") -> Optional["Transaction"]:
        if self.tx_id is None:
            return None
        if self._transaction is None:
            self._transaction = bsq_wallet_service.get_transaction(self.tx_id)
        return self._transaction
        