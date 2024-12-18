from collections.abc import Callable
from datetime import timedelta
from typing import TYPE_CHECKING, Optional, cast
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.locale.res import Res
from bisq.core.network.p2p.ack_message_source_type import AckMessageSourceType
from bisq.core.network.p2p.file_transfer_part import FileTransferPart
from bisq.core.network.p2p.network.message_listener import MessageListener
from bisq.core.support.dispute.agent.dispute_agent_lookup_map import DisputeAgentLookupMap
from bisq.core.support.dispute.dispute import DisputeState
from bisq.core.support.dispute.dispute_manager import DisputeManager

from bisq.core.support.dispute.mediation.mediation_result_state import MediationResultState
from bisq.core.support.dispute.messages.dispute_result_message import (
    DisputeResultMessage,
)
from bisq.core.support.dispute.messages.open_new_dispute_message import (
    OpenNewDisputeMessage,
)
from bisq.core.support.dispute.messages.peer_opened_dispute_message import (
    PeerOpenedDisputeMessage,
)
from bisq.core.support.messages.chat_messsage import ChatMessage
from bisq.core.trade.model.bisq_v1.trade import Trade
from bisq.core.trade.model.trade_dispute_state import TradeDisputeState
from bisq.core.support.support_type import SupportType
import bisq.common.version as Version
from bisq.core.support.dispute.mediation.file_transfer_session import FileTransferSession
from bisq.core.trade.protocol.bisq_v1.dispute_protocol import DisputeProtocol

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_envelope import NetworkEnvelope
    from bisq.core.network.p2p.network.connection import Connection
    from bisq.core.support.dispute.mediation.file_transfer_sender import FileTransferSender
    from bisq.core.support.dispute.mediation.mediation_dispute_list import MediationDisputeList
    from bisq.core.trade.model.bisq_v1.contract import Contract
    from bitcoinj.core.transaction import Transaction
    from bisq.core.support.messages.support_message import SupportMessage
    from bisq.core.support.dispute.dispute import Dispute
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.trade.bisq_v1.failed_trades_manager import FailedTradesManager
    from bisq.core.support.dispute.mediation.mediation_dispute_list_service import (
        MediationDisputeListService,
    )
    from bisq.core.trade.closed_tradable_manager import ClosedTradableManager
    from bisq.common.config.config import Config
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.btc.wallet.trade_wallet_service import TradeWalletService
    from bisq.core.btc.wallets_setup import WalletsSetup
    from bisq.core.dao.dao_facade import DaoFacade
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.offer.open_offer_manager import OpenOfferManager
    from bisq.core.provider.price.price_feed_service import PriceFeedService
    from bisq.core.trade.trade_manager import TradeManager

logger = get_logger(__name__)


class MediationManager(DisputeManager["MediationDisputeList"], MessageListener, FileTransferSession.FtpCallback):
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
        mediation_dispute_list_service: "MediationDisputeListService",
        config: "Config",
        price_feed_service: "PriceFeedService",
    ):
        super().__init__(
            p2p_service,
            trade_wallet_service,
            btc_wallet_service,
            wallets_setup,
            trade_manager,
            closed_tradable_manager,
            failed_trades_manager,
            open_offer_manager,
            dao_facade,
            key_ring,
            mediation_dispute_list_service,
            config,
            price_feed_service,
        )
        
        self.p2p_service.network_node.add_message_listener(self) # listening for FileTransferPart message

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Implement template methods
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_support_type(self) -> SupportType:
        return SupportType.MEDIATION

    def on_support_message(self, message: "SupportMessage") -> None:
        if self.can_process_message(message):
            logger.info(
                f"Received {message.__class__.__name__} with tradeId {message.get_trade_id()} and uid {message.uid}"
            )

            if isinstance(message, OpenNewDisputeMessage):
                self.on_open_new_dispute_message(message)
            elif isinstance(message, PeerOpenedDisputeMessage):
                self.on_peer_opened_dispute_message(message)
            elif isinstance(message, ChatMessage):
                self.on_chat_message(message)
            elif isinstance(message, DisputeResultMessage):
                self.on_dispute_result_message(message)
            else:
                logger.warning(
                    f"Unsupported message at dispatch_message. message={message}"
                )

    def get_dispute_state_started_by_peer(self) -> "TradeDisputeState":
        return TradeDisputeState.MEDIATION_STARTED_BY_PEER

    def get_ack_message_source_type(self) -> AckMessageSourceType:
        return AckMessageSourceType.MEDIATION_MESSAGE

    def cleanup_disputes(self) -> None:
        # closes any trades/disputes which paid out while Bisq was not in use
        def close_trade(trade_id: str) -> None:
            trade = self.trade_manager.get_trade_by_id(trade_id)
            if trade and trade.payout_tx is not None:
                self.trade_manager.close_disputed_trade(
                    trade_id, TradeDisputeState.MEDIATION_CLOSED
                )
                dispute = self.find_own_dispute(trade_id)
                if dispute:
                    dispute.is_closed = True

        self.dispute_list_service.cleanup_disputes(close_trade)

    def get_dispute_info(self, dispute: "Dispute") -> str:
        role = Res.get("shared.mediator").lower()
        agent_node_address = self.get_agent_node_address(dispute)
        assert agent_node_address is not None, "Agent node address must not be None"
        role_context_msg = Res.get(
            "support.initialMediatorMsg",
            DisputeAgentLookupMap.get_matrix_link_for_agent(
                agent_node_address.get_full_address()
            ),
        )
        link = "https://bisq.wiki/Dispute_resolution#Level_2:_Mediation"
        return Res.get("support.initialInfo", role, role_context_msg, role, link)

    def get_dispute_intro_for_peer(self, dispute_info: str) -> str:
        return Res.get(
            "support.peerOpenedDisputeForMediation", dispute_info, Version.VERSION
        )

    def get_dispute_intro_for_dispute_creator(self, dispute_info: str) -> str:
        return Res.get(
            "support.youOpenedDisputeForMediation", dispute_info, Version.VERSION
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Message handler
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # We get that message at both peers. The dispute object is in context of the trader
    def on_dispute_result_message(
        self, dispute_result_message: "DisputeResultMessage"
    ) -> None:
        dispute_result = dispute_result_message.dispute_result
        trade_id = dispute_result.trade_id
        chat_message = dispute_result.chat_message
        assert chat_message is not None, "chatMessage must not be None"
    

        dispute = self.find_dispute(dispute_result)
        uid = dispute_result_message.uid

        if dispute is None:
            logger.warning(
                f"We got a dispute result msg but we don't have a matching dispute. "
                f"That might happen when we get the disputeResultMessage before the dispute was created. "
                f"We try again after 2 sec. to apply the disputeResultMessage. TradeId = {trade_id}"
            )
            if uid not in self.delay_msg_map:
                # We delay 2 sec. to be sure the comm. msg gets added first
                timer = UserThread.run_after(
                    lambda: self.on_dispute_result_message(dispute_result_message),
                    timedelta(seconds=2),
                )
                self.delay_msg_map[uid] = timer
            else:
                logger.warning(
                    f"We got a dispute result msg after we already repeated to apply the message after a delay. "
                    f"That should never happen. TradeId = {trade_id}"
                )
            return

        self.cleanup_retry_map(uid)

        if chat_message not in dispute.chat_messages:
            dispute.add_and_persist_chat_message(chat_message)
        else:
            logger.warning(
                f"We got a dispute mail msg what we have already stored. TradeId = {chat_message.trade_id}"
            )

        dispute.dispute_state_property.value = DisputeState.RESULT_PROPOSED
        dispute.dispute_result_property.value = dispute_result

        trade = self.trade_manager.get_trade_by_id(trade_id)
        
        if trade:
            if trade.dispute_state in [TradeDisputeState.MEDIATION_REQUESTED, TradeDisputeState.MEDIATION_STARTED_BY_PEER]:
                trade.process_model.buyer_payout_amount_from_mediation = dispute_result.buyer_payout_amount
                trade.process_model.seller_payout_amount_from_mediation = dispute_result.seller_payout_amount
                
                trade.dispute_state = TradeDisputeState.MEDIATION_CLOSED
                
                self.trade_manager.request_persistence()
                self.check_for_mediated_trade_payout(trade, dispute)
            else:
                open_offer = self.open_offer_manager.get_open_offer_by_id(trade_id)
                if open_offer:
                    self.open_offer_manager.close_open_offer(open_offer.offer)

        self.send_ack_message(chat_message, dispute.agent_pub_key_ring, True, None)

        self.maybe_clear_sensitive_data()
        self.request_persistence()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_agent_node_address(self, dispute: "Dispute") -> Optional["NodeAddress"]:
        return dispute.contract.mediator_node_address

    def on_accept_mediation_result(
        self,
        trade: "Trade",
        result_handler: Callable[[], None],
        error_message_handler: Callable[[str], None],
    ) -> None:
        trade_id = trade.get_id()
        optional_dispute = self._find_dispute_by_ids(trade_id)
        assert optional_dispute is not None, "dispute must be present"
        dispute_result = optional_dispute.dispute_result_property.value
        buyer_payout_amount = dispute_result.buyer_payout_amount
        seller_payout_amount = dispute_result.seller_payout_amount
        process_model = trade.process_model
        process_model.buyer_payout_amount_from_mediation = buyer_payout_amount
        process_model.seller_payout_amount_from_mediation = seller_payout_amount
        trade_protocol = cast(DisputeProtocol, self.trade_manager.get_trade_protocol(trade)) # get_trade_protocol returns a TradeProtocol that is also DisputeProtocol
        if not isinstance(trade_protocol, DisputeProtocol):
            raise ValueError("TradeProtocol returned from trade_manager.get_trade_protocol must be an instance of DisputeProtocol")

        trade.mediation_result_state_property.value = MediationResultState.MEDIATION_RESULT_ACCEPTED
        self.trade_manager.request_persistence()

        # If we have not got yet the peers signature we sign and send to the peer our signature.
        # Otherwise we sign and complete with the peers signature the payout tx.
        if process_model.trade_peer.mediated_payout_tx_signature is None:
            trade_protocol.on_accept_mediation_result(
                lambda: self._handle_payout_completion(trade, trade_id, result_handler),
                error_message_handler,
            )
        else:
            trade_protocol.on_finalize_mediation_result_payout(
                lambda: self._handle_payout_completion(trade, trade_id, result_handler),
                error_message_handler,
            )

    def _handle_payout_completion(
        self, trade: "Trade", trade_id: str, result_handler: Callable[[], None]
    ) -> None:
        if trade.payout_tx is not None:
            self.trade_manager.close_disputed_trade(
                trade_id, TradeDisputeState.MEDIATION_CLOSED
            )
        result_handler()

    def reject_mediation_result(self, trade: "Trade") -> None:
        trade.mediation_result_state_property.value = MediationResultState.MEDIATION_RESULT_REJECTED
        self.trade_manager.request_persistence()

    def init_log_upload(
        self, callback: "FileTransferSession.FtpCallback", trade_id: str, trader_id: int
    ) -> "FileTransferSender":
        dispute = self._find_dispute_by_ids(trade_id, trader_id)
        if not dispute:
            raise IOError("could not locate Dispute for tradeId/traderId")
        return dispute.create_file_transfer_sender(
            self.p2p_service.network_node,
            dispute.contract.mediator_node_address,
            callback,
        )

    def process_file_part_received(self, ftp: "FileTransferPart") -> None:
        if not ftp.is_initial_request:
            return  # existing sessions are processed by FileTransferSession object directly
        
        # we create a new session which is related to an open dispute from our list
        dispute = self._find_dispute_by_ids(ftp.trade_id, ftp.trader_id)
        if not dispute:
            logger.error(
                f"Received log upload request for unknown TradeId/TraderId {ftp.trade_id}/{ftp.trader_id}"
            )
            return
        
        if dispute.is_closed:
            logger.error(f"Received a file transfer request for closed dispute {ftp.trade_id}")
            return
        
        try:
            session = dispute.create_or_get_file_transfer_receiver(
                self.p2p_service.network_node, ftp.sender_node_address, self
            )
            session.process_file_part_received(ftp)
        except IOError as e:
            logger.error(f"Unable to process a received file message: {e}")

    def on_message(self, network_envelope: "NetworkEnvelope", connection: "Connection") -> None:
        # mediator receiving log file data
        if isinstance(network_envelope, FileTransferPart):
            self.process_file_part_received(network_envelope)

    def on_ftp_progress(self, progress_pct: float) -> None:
        logger.trace(f"ftp progress: {progress_pct}")

    def on_ftp_complete(self, session: "FileTransferSession") -> None:
        dispute = self._find_dispute_by_ids(session.full_trade_id, session.trader_id)
        if dispute:
            self.add_mediation_logs_received_message(dispute, session.zip_id)

    def on_ftp_timeout(self, status_msg: str, session: "FileTransferSession") -> None:
        session.reset_session()

    