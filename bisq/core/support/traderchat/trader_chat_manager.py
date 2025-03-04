from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.core.locale.res import Res
from bisq.core.network.p2p.ack_message_source_type import AckMessageSourceType
from bisq.core.support.support_manager import SupportManager
from bisq.core.support.support_type import SupportType
from bisq.core.support.messages.chat_messsage import ChatMessage
from utils.data import ObservableList

if TYPE_CHECKING:
    from bisq.core.support.messages.support_message import SupportMessage
    from bisq.core.trade.model.bisq_v1.trade import Trade 
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.btc.setup.wallets_setup import WalletsSetup
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.common.crypto.pub_key_ring import PubKeyRing
    from bisq.core.trade.bisq_v1.failed_trades_manager import FailedTradesManager
    from bisq.core.trade.closed_tradable_manager import ClosedTradableManager
    from bisq.core.trade.trade_manager import TradeManager 

logger = get_logger(__name__)

class TraderChatManager(SupportManager):
    def __init__(self, p2p_service: 'P2PService',
                 wallets_setup: 'WalletsSetup',
                 trade_manager: 'TradeManager',
                 closed_tradable_manager: 'ClosedTradableManager',
                 failed_trades_manager: 'FailedTradesManager',
                 pub_key_ring: 'PubKeyRing'):
        super().__init__(p2p_service, wallets_setup)
        self.trade_manager = trade_manager
        self.closed_tradable_manager = closed_tradable_manager
        self.failed_trades_manager = failed_trades_manager
        self.pub_key_ring = pub_key_ring


    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Implement template methods
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_support_type(self):
        return SupportType.TRADE

    def request_persistence(self):
        self.trade_manager.request_persistence()

    def get_peer_node_address(self, message: 'ChatMessage') -> Optional['NodeAddress']:
        trade = self.get_trade_for_chat(message)
        if trade and trade.contract:
            return trade.contract.get_peers_node_address(self.pub_key_ring)
        return None

    def get_peer_pub_key_ring(self, message: 'ChatMessage') -> Optional['PubKeyRing']:
        trade = self.get_trade_for_chat(message)
        if trade and trade.contract:
            return trade.contract.get_peers_pub_key_ring(self.pub_key_ring)
        return None

    def get_all_chat_messages(self, trade_id: str) -> ObservableList['ChatMessage']:
        trade = self.get_trade_by_id(trade_id)
        return trade.chat_messages if trade else ObservableList()

    def channel_open(self, message: 'ChatMessage') -> bool:
        return self.get_trade_for_chat(message) is not None

    def add_and_persist_chat_message(self, message: 'ChatMessage'):
        trade = self.get_trade_for_chat(message)
        if trade:
            chat_messages = trade.chat_messages
            if not any(m.uid == message.uid for m in chat_messages):
                if not chat_messages:
                    self.add_system_msg(trade)
                trade.add_and_persist_chat_message(message)
                self.trade_manager.request_persistence()
            else:
                logger.warning(f"Trade got a chatMessage that we have already stored. UId = {message.uid} TradeId = {message.trade_id}")

    def get_ack_message_source_type(self) -> 'AckMessageSourceType':
        return AckMessageSourceType.TRADE_CHAT_MESSAGE

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_all_services_initialized(self):
        super().on_all_services_initialized()
        self.try_apply_messages()

    def on_support_message(self, message: 'SupportMessage'):
        if self.can_process_message(message):
            logger.info(f"Received {message.__class__.__name__} with tradeId {message.get_trade_id()} and uid {message.uid}")
            if isinstance(message, ChatMessage):
                self.on_chat_message(message)
            else:
                logger.warning(f"Unsupported message at dispatch_message. message={message}")

    def add_system_msg(self, trade: 'Trade'):
        # We need to use the trade date as otherwise our system msg would not be displayed first as the list is sorted
        # by date.
        chat_message = ChatMessage(
            support_type=self.get_support_type(),
            trade_id=trade.get_id(),
            trader_id=0,
            sender_is_trader=False,
            message=Res.get("tradeChat.rules"),
            sender_node_address=NodeAddress.from_full_address("null:0000"),
            date=trade.get_date().timestamp(),
            is_system_message=True
        )
        trade.chat_messages.append(chat_message)
        
        self.request_persistence()

    def get_trade_by_id(self, trade_id: str) -> Optional['Trade']:
        # search for a matching tradeId in open trades, else closed trades, else failed trades
        trade = self.trade_manager.get_trade_by_id(trade_id)
        if not trade:
            trade = next((t for t in self.closed_tradable_manager.get_closed_trades() 
                         if t.get_id() == trade_id), None)
            if not trade:
                trade = self.failed_trades_manager.get_trade_by_id(trade_id)
        return trade

    def get_trade_for_chat(self, message: 'ChatMessage') -> Optional['Trade']:
        return self.get_trade_by_id(message.trade_id)
