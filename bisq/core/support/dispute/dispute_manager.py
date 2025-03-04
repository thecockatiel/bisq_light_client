from abc import ABC, abstractmethod
from datetime import timedelta
from typing import TYPE_CHECKING, Generic, Optional, TypeVar, Union
import uuid
from bisq.common.handlers.fault_handler import FaultHandler
from bisq.common.handlers.result_handler import ResultHandler
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.common.util.math_utils import MathUtils
from bisq.core.btc.wallet.restrictions import Restrictions
from bisq.core.locale.currency_util import is_crypto_currency
from bisq.core.locale.res import Res
from bisq.core.monetary.altcoin import Altcoin
from bisq.core.monetary.price import Price
from bisq.core.network.p2p.bootstrap_listener import BootstrapListener
from bisq.core.network.p2p.send_mailbox_message_listener import SendMailboxMessageListener
from bisq.core.support.dispute.disput_validation_exceptions import DisputeValidationAddressException, DisputeValidationNodeAddressException
from bisq.core.support.dispute.dispute import DisputeState
from bisq.core.support.dispute.dispute_already_open_exception import DisputeAlreadyOpenException
from bisq.core.support.dispute.dispute_message_delivery_failed_exception import DisputeMessageDeliveryFailedException
from bisq.core.support.dispute.dispute_validation import DisputeValidation
from bisq.core.support.dispute.mediation.mediation_result_state import MediationResultState
from bisq.core.trade.bisq_v1.trade_data_validation import TradeDataValidation
from bisq.core.trade.bisq_v1.trade_data_validation_exception import TradeDataValidationException
from bisq.core.trade.model.trade_phase import TradePhase
from bitcoinj.base.coin import Coin
from bitcoinj.base.utils.fiat import Fiat
from utils.data import ObservableList, SimpleProperty, SimplePropertyChangeEvent
from bisq.core.support.support_manager import SupportManager
from bisq.core.support.dispute.disput_validation_exceptions import DisputeValidationException
from bisq.common.version import Version
from utils.time import get_time_ms
from bisq.core.support.messages.chat_messsage import ChatMessage

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.core.support.dispute.messages.dispute_result_message import DisputeResultMessage
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.support.dispute.dispute_list import DisputeList
    from bisq.core.support.dispute.dispute import Dispute 
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.common.config.config import Config
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.btc.wallet.trade_wallet_service import TradeWalletService
    from bisq.core.btc.setup.wallets_setup import WalletsSetup
    from bisq.core.dao.dao_facade import DaoFacade
    from bisq.core.offer.open_offer_manager import OpenOfferManager
    from bisq.core.provider.price.price_feed_service import PriceFeedService
    from bisq.core.support.dispute.dispute_list_service import DisputeListService
    from bisq.core.trade.bisq_v1.failed_trades_manager import FailedTradesManager
    from bisq.core.trade.trade_manager import TradeManager
    from bisq.core.trade.closed_tradable_manager import ClosedTradableManager
    from bisq.common.crypto.pub_key_ring import PubKeyRing
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.trade.model.trade_dispute_state import TradeDisputeState
    from bisq.core.trade.model.bisq_v1.contract import Contract
    from bisq.core.support.dispute.messages.open_new_dispute_message import OpenNewDisputeMessage
    from bisq.core.support.dispute.messages.peer_opened_dispute_message import PeerOpenedDisputeMessage
    from bisq.core.support.dispute.dispute_result import DisputeResult

_T = TypeVar('T', bound='DisputeList[Dispute]')

logger = get_logger(__name__)

class DisputeManager(Generic[_T], SupportManager, ABC):
    def __init__(
        self,
        p2p_service: "P2PService",
        trade_wallet_service: "TradeWalletService",
        btc_wallet_service: "BtcWalletService",
        wallets_setup: "WalletsSetup",
        trade_manager: "TradeManager",
        closed_tradable_manager: "ClosedTradableManager",
        failed_trades_manager: "FailedTradesManager",
        open_offer_manager: "OpenOfferManager",
        dao_facade: "DaoFacade",
        key_ring: "KeyRing",
        dispute_list_service: "DisputeListService",
        config: "Config",
        price_feed_service: "PriceFeedService",
    ):
        super().__init__(p2p_service, wallets_setup)
        
        self.trade_wallet_service = trade_wallet_service
        self.btc_wallet_service = btc_wallet_service
        self.trade_manager = trade_manager
        self.closed_tradable_manager = closed_tradable_manager
        self.failed_trades_manager = failed_trades_manager
        self.open_offer_manager = open_offer_manager
        self.dao_facade = dao_facade
        self.pub_key_ring = key_ring.pub_key_ring
        self.signature_key_pair = key_ring.signature_key_pair
        self.dispute_list_service = dispute_list_service
        self.config = config
        self.price_feed_service = price_feed_service
        
        self.validation_exceptions = ObservableList["DisputeValidationException"]()
        self.pending_outgoing_message: Optional[str] = None
        
        self.clear_pending_message()
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Implement template methods
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def request_persistence(self):
        return self.dispute_list_service.request_persistence()
    
    def get_peer_node_address(self, message: "ChatMessage") -> Optional["NodeAddress"]:
        dispute = self.find_dispute(message)
        if dispute is None:
            logger.warning(f"Could not find dispute for tradeId = {message.trade_id} traderId = {message.trader_id}")
            return None
        return self.get_node_address_pub_key_ring_tuble(dispute)[0]
    
    def get_peer_pub_key_ring(self, message: "ChatMessage") -> Optional["PubKeyRing"]:
        dispute = self.find_dispute(message)
        if dispute is None:
            logger.warning(f"Could not find dispute for tradeId = {message.trade_id} traderId = {message.trader_id}")
            return None
        return self.get_node_address_pub_key_ring_tuble(dispute)[1]
    
    def get_all_chat_messages(self, trade_id: str) -> list["ChatMessage"]:
        messages = []
        for dispute in self.get_dispute_list():
            if dispute.trade_id == trade_id:
                messages.extend(dispute.chat_messages)
        return messages
    
    def channel_open(self, message: "ChatMessage") -> bool:
        return self.find_dispute(message) is not None
    
    def add_and_persist_chat_message(self, message: "ChatMessage") -> None:
        dispute = self.find_dispute(message)
        if dispute:
            if not any(m.uid == message.uid for m in dispute.chat_messages):
                dispute.add_and_persist_chat_message(message)
                self.request_persistence()
            else:
                logger.warning(f"We got a chatMessage that we have already stored. UId = {message.uid} TradeId = {message.trade_id}")

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Abstract methods
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # We get that message at both peers. The dispute object is in context of the trader
    @abstractmethod
    def on_dispute_result_message(self, dispute_result_message: "DisputeResultMessage"):
        pass

    @abstractmethod
    def get_agent_node_address(self, dispute: "Dispute") -> Optional["NodeAddress"]:
        pass

    @abstractmethod
    def get_dispute_state_started_by_peer(self) -> "TradeDisputeState":
        pass

    @abstractmethod
    def cleanup_disputes(self) -> None:
        pass

    @abstractmethod
    def get_dispute_info(self, dispute: "Dispute") -> str:
        pass

    @abstractmethod
    def get_dispute_intro_for_peer(self, dispute_info: str) -> str:
        pass

    @abstractmethod
    def get_dispute_intro_for_dispute_creator(self, dispute_info: str) -> str:
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Delegates for disputeListService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @property
    def num_open_disputes_property(self) -> SimpleProperty[int]:
        return self.dispute_list_service.num_open_disputes_property

    def get_disputes_as_observable_list(self) -> ObservableList["Dispute"]:
        return self.dispute_list_service.get_observable_list()

    def get_nr_of_disputes(self, is_buyer: bool, contract: "Contract") -> str:
        return self.dispute_list_service.get_nr_of_disputes(is_buyer, contract)

    def get_dispute_list(self) -> _T:
        return self.dispute_list_service.dispute_list

    def get_disputed_trade_ids(self) -> set[str]:
        return self.dispute_list_service.disputed_trade_ids

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_all_services_initialized(self):
        super().on_all_services_initialized()
        self.dispute_list_service.on_all_services_initialized()

        class Listener(BootstrapListener):
            def on_data_received(self_):
                self.try_apply_messages()
                self.check_disputes_for_updates()

        self.p2p_service.add_p2p_service_listener(Listener())

        # def on_num_peers_change(e):
        #     if self.wallets_setup.has_sufficient_peers_for_broadcast:
        #         self.try_apply_messages()

        # self.wallets_setup.num_peers_property.add_listener(on_num_peers_change) # TODO: check if this is needed

        self.try_apply_messages()
        self.cleanup_disputes()

        disputes = self.get_dispute_list().list
        for dispute in disputes:
            try:
                DisputeValidation.validate_node_addresses(dispute, self.config)
                if dispute.is_using_legacy_burning_man():
                    DisputeValidation.validate_donation_address_matches_any_past_param_values(
                        dispute, 
                        dispute.donation_address_of_delayed_payout_tx, 
                        self.dao_facade
                    )
            except (DisputeValidationAddressException, DisputeValidationNodeAddressException) as e:
                logger.error(e)
                self.validation_exceptions.append(e)

        def on_dispute_replay_exception(e: Exception):
            logger.error(e)
            self.validation_exceptions.append(e)

        DisputeValidation.test_if_any_dispute_tried_replay(disputes, on_dispute_replay_exception)
        
        self.maybe_clear_sensitive_data()

    def check_disputes_for_updates(self) -> None:
        disputes = self.get_dispute_list().list
        for dispute in disputes:
            if dispute.is_result_proposed:
                # an open dispute where the mediator has proposed a result. has the trade moved on?
                # if so, dispute can close and the mediator needs to be informed so they can close their ticket.
                trade = self.trade_manager.get_trade_by_id(dispute.trade_id)
                if trade:
                    self.check_for_mediated_trade_payout(trade, dispute)
                else:
                    closed_trade = self.closed_tradable_manager.get_tradable_by_id(dispute.trade_id)
                    if closed_trade:
                        self.check_for_mediated_trade_payout(closed_trade, dispute)

    def check_for_mediated_trade_payout(self, trade: "Trade", dispute: "Dispute") -> None:
        if trade.dispute_state.is_arbitrated or trade.get_trade_phase() == TradePhase.PAYOUT_PUBLISHED:
            self.disputed_trade_update(trade.dispute_state.name, dispute, True)
        else:
            def on_mediation_result_change(e: SimplePropertyChangeEvent['MediationResultState']):
                if e.new_value in [MediationResultState.MEDIATION_RESULT_ACCEPTED, MediationResultState.MEDIATION_RESULT_REJECTED]:
                    self.disputed_trade_update(e.new_value.name, dispute, False)

            def on_dispute_state_change(e: SimplePropertyChangeEvent['TradeDisputeState']):
                if e.new_value.is_arbitrated:
                    self.disputed_trade_update(e.new_value.name, dispute, True)

            def on_phase_change(e: SimplePropertyChangeEvent['TradePhase']):
                if e.new_value == TradePhase.PAYOUT_PUBLISHED:
                    self.disputed_trade_update(e.new_value.name, dispute, True)

            # user accepted/rejected mediation proposal (before lockup period has expired)
            trade.mediation_result_state_property.add_listener(on_mediation_result_change)
            # user rejected mediation after lockup period: opening arbitration
            trade.dispute_state_property.add_listener(on_dispute_state_change)
            # trade paid out through mediation
            trade.state_phase_property.add_listener(on_phase_change)

    def is_trader(self, dispute: "Dispute") -> bool:
        return self.pub_key_ring == dispute.trader_pub_key_ring

    def find_own_dispute(self, trade_id: str) -> Optional["Dispute"]:
        dispute_list = self.get_dispute_list()
        if dispute_list is None:
            logger.warning("disputes is None")
            return None
        
        return next((d for d in dispute_list if d.trade_id == trade_id), None)

    def maybe_clear_sensitive_data(self) -> None:
        logger.info(f"{self.__class__.__name__} checking closed disputes eligibility for having sensitive data cleared")
        safe_date = self.closed_tradable_manager.get_safe_date_for_sensitive_data_clearing()
        
        for dispute in self.get_dispute_list().list:
            if dispute.is_closed and dispute.opening_date < int(safe_date.timestamp()*1000):
                dispute.maybe_clear_sensitive_data()
        
        self.request_persistence()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Message handler
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def agent_check_dispute_health(self, dispute_to_check: "Dispute") -> bool:
        # checking from the agent perspective only
        if any(msg.sender_is_trader for msg in dispute_to_check.chat_messages):
            return True

        # consider only messages which have been transmitted
        transmitted_messages = [
            msg for msg in dispute_to_check.chat_messages 
            if not msg.is_system_message and not msg.stored_in_mailbox_property.get()
        ]

        if not transmitted_messages:
            return True

        # dispute is healthy if any transmitted message has been ACKd by the peer
        return any(msg.acknowledged_property.get() for msg in transmitted_messages)

    # dispute agent receives that from trader who opens dispute
    def on_open_new_dispute_message(self, open_new_dispute_message: "OpenNewDisputeMessage") -> None:
        dispute_list = self.get_dispute_list()
        if dispute_list is None:
            logger.warning("dispute_list is None")
            return

        error_message = None
        dispute = open_new_dispute_message.dispute
        # Disputes from clients < 1.2.0 always have support type ARBITRATION in dispute as the field didn't exist before
        dispute.support_type = open_new_dispute_message.support_type
        # disputes from clients < 1.6.0 have state not set as the field didn't exist before
        dispute.dispute_state_property.value = DisputeState.NEW  # this can be removed a few months after 1.6.0 release

        contract = dispute.contract
        self.add_price_info_message(dispute, 0)

        peers_pub_key_ring = contract.seller_pub_key_ring if dispute.dispute_opener_is_buyer else contract.buyer_pub_key_ring
        if self.is_agent(dispute):
            if dispute not in dispute_list:
                stored_dispute = self.find_dispute(dispute)
                if stored_dispute is None:
                    dispute_list.append(dispute)
                    self.send_peer_opened_dispute_message(dispute, contract, peers_pub_key_ring)
                else:
                    # valid case if both have opened a dispute and agent was not online.
                    logger.debug(f"We got a dispute already open for that trade and trading peer. TradeId = {dispute.trade_id}")
            else:
                error_message = f"We got a dispute msg what we have already stored. TradeId = {dispute.trade_id}"
                logger.warning(error_message)
        else:
            error_message = "Trader received openNewDisputeMessage. That must never happen."
            logger.error(error_message)

        # We use the ChatMessage not the openNewDisputeMessage for the ACK
        messages = dispute.chat_messages
        if messages:
            chat_message = messages[0]
            senders_pub_key_ring = contract.buyer_pub_key_ring if dispute.dispute_opener_is_buyer else contract.seller_pub_key_ring
            self.send_ack_message(chat_message, senders_pub_key_ring, error_message is None, error_message)

        self.add_mediation_result_message(dispute)

        try:
            DisputeValidation.validate_dispute_data(dispute, self.btc_wallet_service)
            DisputeValidation.validate_node_addresses(dispute, self.config)
            DisputeValidation.validate_sender_node_address(dispute, open_new_dispute_message.sender_node_address)
            DisputeValidation.test_if_dispute_tries_replay(dispute, dispute_list.list)
            if dispute.is_using_legacy_burning_man():
                DisputeValidation.validate_donation_address_matches_any_past_param_values(
                    dispute, 
                    dispute.donation_address_of_delayed_payout_tx, 
                    self.dao_facade
                )
        except DisputeValidationException as e:
            logger.error(e)
            self.validation_exceptions.append(e)
            
        self.request_persistence()

    # Not-dispute-requester receives that msg from dispute agent
    def on_peer_opened_dispute_message(self, peer_opened_dispute_message: "PeerOpenedDisputeMessage") -> None:
        dispute = peer_opened_dispute_message.dispute
        trade = self.trade_manager.get_trade_by_id(dispute.trade_id)
        if trade:
            self.peer_opened_dispute_for_trade(peer_opened_dispute_message, dispute, trade)
        else:
            closed_trade = self.closed_tradable_manager.get_tradable_by_id(dispute.trade_id)
            if closed_trade:
                self.new_dispute_reverts_closed_trade(peer_opened_dispute_message, dispute, closed_trade)
            else:
                failed_trade = self.failed_trades_manager.get_trade_by_id(dispute.trade_id)
                if failed_trade:
                    self.new_dispute_reverts_failed_trade(peer_opened_dispute_message, dispute, failed_trade)

    def new_dispute_reverts_failed_trade(self, peer_opened_dispute_message: "PeerOpenedDisputeMessage", 
                                       dispute: "Dispute", trade: "Trade") -> None:
        logger.info(f"Peer dispute ticket received, reverting failed trade {trade.get_short_id()} to pending")
        self.failed_trades_manager.remove_trade(trade)
        self.trade_manager.add_trade_to_pending_trades(trade)
        self.peer_opened_dispute_for_trade(peer_opened_dispute_message, dispute, trade)

    def new_dispute_reverts_closed_trade(self, peer_opened_dispute_message: "PeerOpenedDisputeMessage", 
                                       dispute: "Dispute", trade: "Trade") -> None:
        logger.info(f"Peer dispute ticket received, reverting closed trade {trade.get_short_id()} to pending")
        self.closed_tradable_manager.remove(trade)
        self.trade_manager.add_trade_to_pending_trades(trade)
        self.peer_opened_dispute_for_trade(peer_opened_dispute_message, dispute, trade)

    def peer_opened_dispute_for_trade(self, peer_opened_dispute_message: "PeerOpenedDisputeMessage", 
                                    dispute: "Dispute", trade: "Trade") -> None:
        error_message = None
        dispute_list = self.get_dispute_list()
        if dispute_list is None:
            logger.warning("disputes is None")
            return

        try:
            DisputeValidation.validate_dispute_data(dispute, self.btc_wallet_service)
            DisputeValidation.validate_node_addresses(dispute, self.config)
            DisputeValidation.validate_trade_and_dispute(dispute, trade)
            TradeDataValidation.validate_delayed_payout_tx(trade, trade.delayed_payout_tx, self.btc_wallet_service)
            if dispute.is_using_legacy_burning_man():
                DisputeValidation.validate_donation_address(dispute, trade.delayed_payout_tx, self.btc_wallet_service.params)
                DisputeValidation.validate_donation_address_matches_any_past_param_values(
                    dispute, 
                    dispute.donation_address_of_delayed_payout_tx, 
                    self.dao_facade
                )
        except (TradeDataValidationException, DisputeValidationException) as e:
            # The peer sent us an invalid donation address. We do not return here as we don't want to break
            # mediation/arbitration and log only the issue. The dispute agent will run validation as well and will get
            # a popup displayed to react.
            logger.warning(f"Donation address is invalid. {e}")

        if not self.is_agent(dispute):
            if dispute not in dispute_list:
                stored_dispute = self.find_dispute(dispute)
                if not stored_dispute:
                    dispute_list.append(dispute)
                    trade.dispute_state = self.get_dispute_state_started_by_peer()
                    self.trade_manager.request_persistence()
                else:
                    # valid case if both have opened a dispute and agent was not online.
                    logger.debug(f"We got a dispute already open for that trade and trading peer. TradeId = {dispute.trade_id}")
            else:
                error_message = f"We got a dispute msg what we have already stored. TradeId = {dispute.trade_id}"
                logger.warning(error_message)
        else:
            error_message = "Arbitrator received peerOpenedDisputeMessage. That must never happen."
            logger.error(error_message)

        # We use the ChatMessage not the peerOpenedDisputeMessage for the ACK
        messages = dispute.chat_messages
        if messages:
            msg = messages[0]
            self.send_ack_message(msg, dispute.agent_pub_key_ring, error_message is None, error_message)

        self.send_ack_message(peer_opened_dispute_message, dispute.agent_pub_key_ring, error_message is None, error_message)
        self.request_persistence()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Send message
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def send_open_new_dispute_message(self, dispute: "Dispute", re_open: bool, result_handler: ResultHandler, fault_handler: FaultHandler) -> None:
        dispute_list = self.get_dispute_list()
        if dispute_list is None:
            logger.warning("disputes is None")
            return

        if dispute in dispute_list:
            msg = f"We got a dispute msg what we have already stored. TradeId = {dispute.trade_id}"
            logger.warning(msg)
            fault_handler(msg, DisputeAlreadyOpenException())
            return

        stored_dispute = self.find_dispute(dispute)
        if stored_dispute is None or re_open:
            dispute_info = self.get_dispute_info(dispute)
            dispute_message = self.get_dispute_intro_for_dispute_creator(dispute_info)
            if dispute.is_support_ticket:
                sys_msg = Res.get("support.youOpenedTicket", dispute_info, Version.VERSION)
            else:
                sys_msg = dispute_message

            message = Res.get("support.systemMsg", sys_msg)
            chat_message = ChatMessage(
                support_type=self.get_support_type(),
                trade_id=dispute.trade_id,
                trader_id=hash(self.pub_key_ring),
                sender_is_trader=False,
                message=message,
                sender_node_address=self.p2p_service.address
            )
            chat_message.is_system_message = True
            dispute.add_and_persist_chat_message(chat_message)
            
            if not re_open:
                dispute_list.append(dispute)

            agent_node_address = self.get_agent_node_address(dispute)
            if agent_node_address is None:
                return

            open_new_dispute_message = OpenNewDisputeMessage(
                dispute=dispute,
                sender_node_address=self.p2p_service.address,
                uid=str(uuid.uuid4()),
                support_type=self.get_support_type()
            )

            logger.info(
                f"Send {open_new_dispute_message.__class__.__name__} to peer {agent_node_address}. "
                f"tradeId={open_new_dispute_message.get_trade_id()}, "
                f"openNewDisputeMessage.uid={open_new_dispute_message.uid}, "
                f"chatMessage.uid={chat_message.uid}"
            )

            self.record_pending_message(open_new_dispute_message.__class__.__name__)
            
            class Listener(SendMailboxMessageListener):
                def on_arrived(self_):
                    logger.info(
                        f"{open_new_dispute_message.__class__.__name__} arrived at peer {agent_node_address}. "
                        f"tradeId={open_new_dispute_message.get_trade_id()}, "
                        f"openNewDisputeMessage.uid={open_new_dispute_message.uid}, "
                        f"chatMessage.uid={chat_message.uid}"
                    )
                    self.clear_pending_message()
                    # We use the chatMessage wrapped inside the openNewDisputeMessage for
                    # the state, as that is displayed to the user and we only persist that msg
                    chat_message.set_arrived(True)
                    self.request_persistence()
                    result_handler()

                def on_stored_in_mailbox(self_):
                    logger.info(
                        f"{open_new_dispute_message.__class__.__name__} stored in mailbox for peer {agent_node_address}. "
                        f"tradeId={open_new_dispute_message.get_trade_id()}, "
                        f"openNewDisputeMessage.uid={open_new_dispute_message.uid}, "
                        f"chatMessage.uid={chat_message.uid}"
                    )
                    self.clear_pending_message()
                    # We use the chatMessage wrapped inside the openNewDisputeMessage for
                    # the state, as that is displayed to the user and we only persist that msg
                    chat_message.set_stored_in_mailbox(True)
                    self.request_persistence()
                    result_handler()

                def on_fault(self_, error_message: str):
                    logger.error(
                        f"{open_new_dispute_message.__class__.__name__} failed: Peer {agent_node_address}. "
                        f"tradeId={open_new_dispute_message.get_trade_id()}, "
                        f"openNewDisputeMessage.uid={open_new_dispute_message.uid}, "
                        f"chatMessage.uid={chat_message.uid}, "
                        f"errorMessage={error_message}"
                    )
                    self.clear_pending_message()
                    # We use the chatMessage wrapped inside the openNewDisputeMessage for
                    # the state, as that is displayed to the user and we only persist that msg
                    chat_message.set_send_message_error(error_message)
                    self.request_persistence()
                    fault_handler(
                        f"Sending dispute message failed: {error_message}",
                        DisputeMessageDeliveryFailedException()
                    )

            self.mailbox_message_service.send_encrypted_mailbox_message(
                agent_node_address,
                dispute.agent_pub_key_ring,
                open_new_dispute_message,
                Listener()
            )
        else:
            msg = (f"We got a dispute already open for that trade and trading peer.\n"
                  f"TradeId = {dispute.trade_id}")
            logger.warning(msg)
            fault_handler(msg, DisputeAlreadyOpenException())

        self.request_persistence()

    # Dispute agent sends that to trading peer when he received openDispute request
    def send_peer_opened_dispute_message(self, dispute_from_opener: "Dispute", 
                                       contract_from_opener: "Contract", 
                                       pub_key_ring: "PubKeyRing") -> None:
        # We delay a bit for sending the message to the peer to allow that a openDispute message from the peer is
        # being used as the valid msg. If dispute agent was offline and both peer requested we want to see the correct
        # message and not skip the system message of the peer as it would be the case if we have created the system msg
        # from the code below.
        UserThread.run_after(lambda: self.do_send_peer_opened_dispute_message(dispute_from_opener, contract_from_opener, pub_key_ring), timedelta(milliseconds=100))

    def do_send_peer_opened_dispute_message(self, dispute_from_opener: "Dispute",
                                          contract_from_opener: "Contract",
                                          pub_key_ring: "PubKeyRing") -> None:
        dispute_list = self.get_dispute_list()
        if dispute_list is None:
            logger.warning("disputes is None")
            return

        dispute = Dispute(
            opening_date=get_time_ms(),
            trade_id=dispute_from_opener.trade_id,
            trader_id=hash(pub_key_ring),
            dispute_opener_is_buyer=not dispute_from_opener.dispute_opener_is_buyer,
            dispute_opener_is_maker=not dispute_from_opener.dispute_opener_is_maker,
            trader_pub_key_ring=pub_key_ring,
            trade_date=dispute_from_opener.trade_date,
            trade_period_end=dispute_from_opener.trade_period_end,
            contract=contract_from_opener,
            contract_hash=dispute_from_opener.contract_hash,
            deposit_tx_serialized=dispute_from_opener.deposit_tx_serialized,
            payout_tx_serialized=dispute_from_opener.payout_tx_serialized,
            deposit_tx_id=dispute_from_opener.deposit_tx_id,
            payout_tx_id=dispute_from_opener.payout_tx_id,
            contract_as_json=dispute_from_opener.contract_as_json,
            maker_contract_signature=dispute_from_opener.maker_contract_signature,
            taker_contract_signature=dispute_from_opener.taker_contract_signature,
            agent_pub_key_ring=dispute_from_opener.agent_pub_key_ring,
            is_support_ticket=dispute_from_opener.is_support_ticket,
            support_type=dispute_from_opener.support_type
        )

        dispute.extra_data_map = dispute_from_opener.extra_data_map
        dispute.delayed_payout_tx_id = dispute_from_opener.delayed_payout_tx_id
        dispute.donation_address_of_delayed_payout_tx = dispute_from_opener.donation_address_of_delayed_payout_tx
        dispute.burning_man_selection_height = dispute_from_opener.burning_man_selection_height
        dispute.trade_tx_fee = dispute_from_opener.trade_tx_fee

        stored_dispute = self.find_dispute(dispute)
        
        # Valid case if both have opened a dispute and agent was not online
        if stored_dispute:
            logger.info(f"We got a dispute already open for that trade and trading peer. TradeId = {dispute.trade_id}")
            return

        dispute_info = self.get_dispute_info(dispute)
        dispute_message = self.get_dispute_intro_for_peer(dispute_info)
        
        if dispute.is_support_ticket:
            sys_msg = Res.get("support.peerOpenedTicket", dispute_info, Version.VERSION)
        else:
            sys_msg = dispute_message
            
        chat_message = ChatMessage(
            support_type=self.get_support_type(),
            trade_id=dispute.trade_id,
            trader_id=hash(pub_key_ring),
            sender_is_trader=False,
            message=Res.get("support.systemMsg", sys_msg),
            sender_node_address=self.p2p_service.address
        )
        chat_message.is_system_message = True
        dispute.add_and_persist_chat_message(chat_message)

        dispute_list.append(dispute)
        self.send_dispute_opening_msg(dispute)

    def send_dispute_opening_msg(self, dispute: "Dispute") -> None:
        # We mirrored dispute already!
        chat_message = dispute.chat_messages[0]
        contract = dispute.contract
        peers_pub_key_ring = contract.buyer_pub_key_ring if dispute.dispute_opener_is_buyer else contract.seller_pub_key_ring
        peers_node_address = contract.buyer_node_address if dispute.dispute_opener_is_buyer else contract.seller_node_address

        peer_opened_dispute_message = PeerOpenedDisputeMessage(
            dispute=dispute,
            sender_node_address=self.p2p_service.address,
            uid=str(uuid.uuid4()),
            support_type=self.get_support_type()
        )

        logger.info(
            f"Send {peer_opened_dispute_message.__class__.__name__} to peer {peers_node_address}. "
            f"tradeId={peer_opened_dispute_message.get_trade_id()}, "
            f"peerOpenedDisputeMessage.uid={peer_opened_dispute_message.uid}, "
            f"chatMessage.uid={chat_message.uid}"
        )

        self.record_pending_message(peer_opened_dispute_message.__class__.__name__)

        class Listener(SendMailboxMessageListener):
            def on_arrived(self_):
                logger.info(
                    f"{peer_opened_dispute_message.__class__.__name__} arrived at peer {peers_node_address}. "
                    f"tradeId={peer_opened_dispute_message.get_trade_id()}, "
                    f"peerOpenedDisputeMessage.uid={peer_opened_dispute_message.uid}, "
                    f"chatMessage.uid={chat_message.uid}"
                )
                self.clear_pending_message()
                # We use the chatMessage wrapped inside the peerOpenedDisputeMessage for
                # the state, as that is displayed to the user and we only persist that msg
                chat_message.set_arrived(True)
                self.request_persistence()

            def on_stored_in_mailbox(self_):
                logger.info(
                    f"{peer_opened_dispute_message.__class__.__name__} stored in mailbox for peer {peers_node_address}. "
                    f"tradeId={peer_opened_dispute_message.get_trade_id()}, "
                    f"peerOpenedDisputeMessage.uid={peer_opened_dispute_message.uid}, "
                    f"chatMessage.uid={chat_message.uid}"
                )
                self.clear_pending_message()
                # We use the chatMessage wrapped inside the peerOpenedDisputeMessage for
                # the state, as that is displayed to the user and we only persist that msg
                chat_message.set_stored_in_mailbox(True)
                self.request_persistence()

            def on_fault(self_, error_message: str):
                logger.error(
                    f"{peer_opened_dispute_message.__class__.__name__} failed: Peer {peers_node_address}. "
                    f"tradeId={peer_opened_dispute_message.get_trade_id()}, "
                    f"peerOpenedDisputeMessage.uid={peer_opened_dispute_message.uid}, "
                    f"chatMessage.uid={chat_message.uid}, "
                    f"errorMessage={error_message}"
                )
                self.clear_pending_message()
                # We use the chatMessage wrapped inside the peerOpenedDisputeMessage for
                # the state, as that is displayed to the user and we only persist that msg
                chat_message.set_send_message_error(error_message)
                self.request_persistence()

        self.mailbox_message_service.send_encrypted_mailbox_message(
            peers_node_address,
            peers_pub_key_ring,
            peer_opened_dispute_message,
            Listener()
        )
        self.add_price_info_message(dispute, 0)
        self.request_persistence()

    #  dispute agent send result to trader
    def send_dispute_result_message(self, dispute_result: "DisputeResult", dispute: "Dispute", summary_text: str) -> None:
        dispute_list = self.get_dispute_list()
        if dispute_list is None:
            logger.warning("disputes is None")
            return

        chat_message = ChatMessage(
            support_type=self.get_support_type(),
            trade_id=dispute.trade_id,
            trader_id=hash(dispute.trader_pub_key_ring),
            sender_is_trader=False,
            message=summary_text,
            sender_node_address=self.p2p_service.address
        )

        dispute_result.chat_message = chat_message
        dispute.add_and_persist_chat_message(chat_message)

        contract = dispute.contract
        if contract.buyer_pub_key_ring == dispute.trader_pub_key_ring:
            peers_node_address = contract.buyer_node_address
        else:
            peers_node_address = contract.seller_node_address

        dispute_result_message = DisputeResultMessage(
            dispute_result=dispute_result,
            sender_node_address=self.p2p_service.address,
            uid=str(uuid.uuid4()),
            support_type=self.get_support_type()
        )

        logger.info(
            f"Send {dispute_result_message.__class__.__name__} to peer {peers_node_address}. "
            f"tradeId={dispute_result_message.get_trade_id()}, "
            f"disputeResultMessage.uid={dispute_result_message.uid}, "
            f"chatMessage.uid={chat_message.uid}"
        )

        self.record_pending_message(dispute_result_message.__class__.__name__)

        class Listener(SendMailboxMessageListener):
            def on_arrived(self_):
                logger.info(
                    f"{dispute_result_message.__class__.__name__} arrived at peer {peers_node_address}. "
                    f"tradeId={dispute_result_message.get_trade_id()}, "
                    f"disputeResultMessage.uid={dispute_result_message.uid}, "
                    f"chatMessage.uid={chat_message.uid}"
                )
                self.clear_pending_message()
                # We use the chatMessage wrapped inside the disputeResultMessage for
                # the state, as that is displayed to the user and we only persist that msg
                chat_message.set_arrived(True)
                self.request_persistence()

            def on_stored_in_mailbox(self_):
                logger.info(
                    f"{dispute_result_message.__class__.__name__} stored in mailbox for peer {peers_node_address}. "
                    f"tradeId={dispute_result_message.get_trade_id()}, "
                    f"disputeResultMessage.uid={dispute_result_message.uid}, "
                    f"chatMessage.uid={chat_message.uid}"
                )
                self.clear_pending_message()
                # We use the chatMessage wrapped inside the disputeResultMessage for
                # the state, as that is displayed to the user and we only persist that msg
                chat_message.set_stored_in_mailbox(True)
                self.request_persistence()

            def on_fault(self_, error_message: str):
                logger.error(
                    f"{dispute_result_message.__class__.__name__} failed: Peer {peers_node_address}. "
                    f"tradeId={dispute_result_message.get_trade_id()}, "
                    f"disputeResultMessage.uid={dispute_result_message.uid}, "
                    f"chatMessage.uid={chat_message.uid}, "
                    f"errorMessage={error_message}"
                )
                self.clear_pending_message()
                # We use the chatMessage wrapped inside the disputeResultMessage for
                # the state, as that is displayed to the user and we only persist that msg
                chat_message.set_send_message_error(error_message)
                self.request_persistence()

        self.mailbox_message_service.send_encrypted_mailbox_message(
            peers_node_address,
            dispute.trader_pub_key_ring,
            dispute_result_message,
            Listener()
        )
        self.request_persistence()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Utils
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_node_address_pub_key_ring_tuble(self, dispute: "Dispute") -> tuple[Optional["NodeAddress"], Optional["PubKeyRing"]]:
        receiver_pub_key_ring = None
        peer_node_address = None
        if self.is_trader(dispute):
            receiver_pub_key_ring = dispute.agent_pub_key_ring
            peer_node_address = self.get_agent_node_address(dispute)
        elif self.is_agent(dispute):
            receiver_pub_key_ring = dispute.trader_pub_key_ring
            contract = dispute.contract
            if contract.buyer_pub_key_ring == receiver_pub_key_ring:
                peer_node_address = contract.buyer_node_address
            else:
                peer_node_address = contract.seller_node_address
        else:
            logger.error("That must not happen. Trader cannot communicate to other trader.")
        
        return (peer_node_address, receiver_pub_key_ring)

    def is_agent(self, dispute: "Dispute") -> bool:
        return self.pub_key_ring == dispute.agent_pub_key_ring

    def find_dispute(self, item: Union["Dispute", "DisputeResult", "ChatMessage"]) -> Optional["Dispute"]:
        """Find dispute by trade ID and trader ID from a Dispute, DisputeResult, or ChatMessage object"""
        if isinstance(item, str):
            # If passed a trade_id string
            dispute_list = self.get_dispute_list()
            if dispute_list is None:
                logger.warning("disputes is None")
                return None
            return next((d for d in dispute_list if d.trade_id == item), None)
            
        if hasattr(item, 'trade_id') and hasattr(item, 'trader_id'):
            # For Dispute or ChatMessage objects
            return self._find_dispute_by_ids(item.trade_id, item.trader_id)
            
        if hasattr(item, 'chat_message'):
            # For DisputeResult objects
            if item.chat_message is None:
                raise ValueError("chatMessage must not be None")
            return self._find_dispute_by_ids(item.trade_id, item.trader_id)
            
        return None

    def _find_dispute_by_ids(self, trade_id: str, trader_id: Optional[int] = None) -> Optional["Dispute"]:
        dispute_list = self.get_dispute_list()
        if dispute_list is None:
            logger.warning("disputes is None") 
            return None
        if trader_id is None:
            return next((d for d in dispute_list if d.trade_id == trade_id), None)
        else:
            return next((d for d in dispute_list if d.trade_id == trade_id and d.trader_id == trader_id), None)
    
    def find_trade(self, dispute: "Dispute") -> Optional["Trade"]:
        ret_val = self.trade_manager.get_trade_by_id(dispute.trade_id)
        if ret_val is None:
            ret_val = next((e for e in self.closed_tradable_manager.get_closed_trades() 
                          if e.get_id() == dispute.trade_id), None)
        return ret_val

    def add_mediation_result_message(self, dispute: "Dispute") -> None:
        # In case of refundAgent we add a message with the mediatorsDisputeSummary. Only visible for refundAgent.
        if dispute.mediators_dispute_result is not None:
            mediators_dispute_result = Res.get("support.mediatorsDisputeSummary", dispute.mediators_dispute_result)
            mediators_dispute_result_message = ChatMessage(
                support_type=self.get_support_type(),
                trade_id=dispute.trade_id,
                trader_id=hash(self.pub_key_ring),
                sender_is_trader=False,
                message=mediators_dispute_result,
                sender_node_address=self.p2p_service.address
            )
            mediators_dispute_result_message.is_system_message = True
            dispute.add_and_persist_chat_message(mediators_dispute_result_message)
            self.request_persistence()

    # when a mediated trade changes, send a system message informing the mediator, so they can maybe close their ticket.
    def disputed_trade_update(self, message: str, dispute: "Dispute", close: bool) -> None:
        if dispute.is_closed:
            return
            
        chat_message = ChatMessage(
            support_type=self.get_support_type(),
            trade_id=dispute.trade_id,
            trader_id=dispute.trader_id,
            sender_is_trader=True,
            message=Res.get("support.info.disputedTradeUpdate", message),
            sender_node_address=self.p2p_service.address
        )
        chat_message.is_system_message = True
        self.send_chat_message(chat_message)  # inform the mediator
        if close:
            dispute.set_closed() # close the trader's ticket
        self.request_persistence()

    def add_mediation_logs_received_message(self, dispute: "Dispute", logs_identifier: str) -> None:
        logs_received_message = Res.get("support.mediatorReceivedLogs", logs_identifier)
        chat_message = ChatMessage(
            support_type=self.get_support_type(),
            trade_id=dispute.trade_id,
            trader_id=hash(self.pub_key_ring),
            sender_is_trader=False,
            message=logs_received_message,
            sender_node_address=self.p2p_service.address
        )
        chat_message.is_system_message = True
        dispute.add_and_persist_chat_message(chat_message)
        self.request_persistence()

    # If price was going down between take offer time and open dispute time the buyer has an incentive to
    # not send the payment but to try to make a new trade with the better price. We risks to lose part of the
    # security deposit (in mediation we will always get back 0.003 BTC to keep some incentive to accept mediated
    # proposal). But if gain is larger than this loss he has economically an incentive to default in the trade.
    # We do all those calculations to give a hint to mediators to detect option trades.
    def add_price_info_message(self, dispute: "Dispute", counter: int = 0) -> None:
        if not self.price_feed_service.has_prices:
            if counter < 3:
                logger.info("Price provider has still no data. This is expected at startup. We try again in 10 sec.")
                UserThread.run_after(lambda: self.add_price_info_message(dispute, counter + 1), timedelta(seconds=10))
            else:
                logger.warning("Price provider still has no data after 3 repeated requests and 30 seconds delay. We give up.")
            return

        contract = dispute.contract
        offer_payload = contract.offer_payload
        price_at_dispute_opening = self.get_price(offer_payload.currency_code)
        if price_at_dispute_opening is None:
            logger.info(
                f"Price provider did not provide a price for {offer_payload.currency_code}. "
                "This is expected if this currency is not supported by the price providers."
            )
            return

        # The amount we would get if we do a new trade with current price
        potential_amount_at_dispute_opening = price_at_dispute_opening.get_amount_by_volume(contract.get_trade_volume())
        buyer_security_deposit = Coin.value_of(offer_payload.buyer_security_deposit)
        min_refund_at_mediated_dispute = Restrictions.get_min_refund_at_mediated_dispute(contract.trade_amount)
        # minRefundAtMediatedDispute is always larger as buyerSecurityDeposit at mediated payout, 
        # we ignore refund agent case here as there it can be 0.
        max_loss_sec_deposit = buyer_security_deposit.subtract(min_refund_at_mediated_dispute)
        trade_amount = contract.get_trade_amount()
        potential_gain = potential_amount_at_dispute_opening.subtract(trade_amount).subtract(max_loss_sec_deposit)

        # We don't translate those strings (yet) as it is only displayed to mediators/arbitrators
        if potential_gain.is_positive():
            headline = "This might be a potential option trade!"
            option_trade_details = (
                f"\nBTC amount calculated with price at dispute opening: {potential_amount_at_dispute_opening.to_friendly_string()}"
                f"\nMax loss of security deposit is: {max_loss_sec_deposit.to_friendly_string()}"
                f"\nPossible gain from an option trade is: {potential_gain.to_friendly_string()}"
            )
        else:
            headline = "It does not appear to be an option trade."
            option_trade_details = (
                f"\nBTC amount calculated with price at dispute opening: {potential_amount_at_dispute_opening.to_friendly_string()}"
                f"\nMax loss of security deposit is: {max_loss_sec_deposit.to_friendly_string()}"
                f"\nPossible loss from an option trade is: {potential_gain.multiply(-1).to_friendly_string()}"
            )

        percentage_price_details = (
            f" (market based price was used: {offer_payload.market_price_margin * 100}%)"
            if offer_payload.use_market_based_price
            else " (fix price was used)"
        )

        price_info_text = (
            f"System message: {headline}\n\n"
            f"Trade price: {contract.get_trade_price().to_friendly_string()}{percentage_price_details}\n"
            f"Trade amount: {trade_amount.to_friendly_string()}\n"
            f"Price at dispute opening: {price_at_dispute_opening.to_friendly_string()}"
            f"{option_trade_details}"
        )

        # We use the existing msg to copy over the users data
        price_info_message = ChatMessage(
            support_type=self.get_support_type(),
            trade_id=dispute.trade_id,
            trader_id=hash(self.pub_key_ring),
            sender_is_trader=False,
            message=price_info_text,
            sender_node_address=self.p2p_service.address
        )
        price_info_message.is_system_message = True
        dispute.add_and_persist_chat_message(price_info_message)
        self.request_persistence()

    def get_price(self, currency_code: str) -> Optional["Price"]:
        market_price = self.price_feed_service.get_market_price(currency_code)
        if market_price is not None and market_price.is_recent_external_price_available:
            market_price_as_double = market_price.price
            try:
                precision = (Altcoin.SMALLEST_UNIT_EXPONENT 
                           if is_crypto_currency(currency_code)
                           else Fiat.SMALLEST_UNIT_EXPONENT)
                scaled = MathUtils.scale_up_by_power_of_10(market_price_as_double, precision)
                rounded_to_long = MathUtils.round_double_to_long(scaled)
                return Price.value_of(currency_code, rounded_to_long)
            except Exception as e:
                logger.error(f"Exception at get_price / parse_to_fiat: {e}")
                return None
        else:
            return None

    def has_pending_message_at_shutdown(self) -> bool:
        if len(self.pending_outgoing_message) > 0:
            logger.warning(f"{self.__class__.__name__} has an outgoing message pending: {self.pending_outgoing_message}")
            return True
        return False

    def record_pending_message(self, class_name: str) -> None:
        self.pending_outgoing_message = class_name

    def clear_pending_message(self) -> None:
        self.pending_outgoing_message = ""

