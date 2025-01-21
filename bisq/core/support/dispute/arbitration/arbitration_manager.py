from datetime import timedelta
from typing import TYPE_CHECKING, Optional
import uuid
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.btc.exceptions.transaction_verification_exception import TransactionVerificationException
from bisq.core.btc.exceptions.wallet_exception import WalletException
from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.locale.res import Res
from bisq.core.network.p2p.ack_message_source_type import AckMessageSourceType
from bisq.core.network.p2p.send_mailbox_message_listener import (
    SendMailboxMessageListener,
)
from bisq.core.support.dispute.arbitration.arbitration_dispute_list import (
    ArbitrationDisputeList,
)
from bisq.core.support.dispute.arbitration.messages.peer_published_dispute_payout_tx_message import (
    PeerPublishedDisputePayoutTxMessage,
)
from bisq.core.support.dispute.dispute_manager import DisputeManager
from bisq.core.support.dispute.dispute_result_winner import DisputeResultWinner
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
from bisq.common.version import Version
from bitcoinj.core.address_format_exception import AddressFormatException
from bitcoinj.core.signature_decode_exception import SignatureDecodeException

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.contract import Contract
    from bitcoinj.core.transaction import Transaction
    from bisq.core.support.messages.support_message import SupportMessage
    from bisq.core.support.dispute.dispute import Dispute
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.trade.bisq_v1.failed_trades_manager import FailedTradesManager
    from bisq.core.support.dispute.arbitration.arbitration_dispute_list_service import (
        ArbitrationDisputeListService,
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


class ArbitrationManager(DisputeManager["ArbitrationDisputeList"]):
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
        arbitration_dispute_list_service: "ArbitrationDisputeListService",
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
            arbitration_dispute_list_service,
            config,
            price_feed_service,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Implement template methods
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_support_type(self) -> SupportType:
        return SupportType.ARBITRATION

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
            elif isinstance(message, PeerPublishedDisputePayoutTxMessage):
                self.on_disputed_payout_tx_message(message)
            else:
                logger.warning(
                    f"Unsupported message at dispatch_message. message={message}"
                )

    def get_agent_node_address(self, dispute: "Dispute") -> Optional["NodeAddress"]:
        return None

    def get_dispute_state_started_by_peer(self) -> "TradeDisputeState":
        return TradeDisputeState.DISPUTE_STARTED_BY_PEER

    def get_ack_message_source_type(self) -> AckMessageSourceType:
        return AckMessageSourceType.ARBITRATION_MESSAGE

    def cleanup_disputes(self) -> None:
        self.dispute_list_service.cleanup_disputes(
            lambda trade_id: self.trade_manager.close_disputed_trade(
                trade_id, TradeDisputeState.DISPUTE_CLOSED
            )
        )

    def get_dispute_info(self, dispute: "Dispute") -> str:
        role = Res.get("shared.arbitrator").lower()
        link = "https://bisq.wiki/Arbitrator#Arbitrator_versus_Legacy_Arbitrator"
        # Arbitration is not used anymore
        return Res.get(
            "support.initialInfo", role, "", role, link
        )  

    def get_dispute_intro_for_peer(self, dispute_info: str) -> str:
        return Res.get("support.peerOpenedDispute", dispute_info, Version.VERSION)

    def get_dispute_intro_for_dispute_creator(self, dispute_info: str) -> str:
        return Res.get("support.youOpenedDispute", dispute_info, Version.VERSION)

    def add_price_info_message(self, dispute: "Dispute", counter: int) -> None:
        # Arbitrator is not used anymore.
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Message handler
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # We get that message at both peers. The dispute object is in context of the trader
    def on_dispute_result_message(
        self, dispute_result_message: "DisputeResultMessage"
    ) -> None:
        dispute_result = dispute_result_message.dispute_result
        chat_message = dispute_result.chat_message
        assert chat_message is not None, "chatMessage must not be None"
        
        if (
            dispute_result.arbitrator_pub_key
            == self.btc_wallet_service.get_arbitrator_address_entry().pub_key
        ):
            logger.error(
                "Arbitrator received disputeResultMessage. That must never happen."
            )
            return

        trade_id = dispute_result.trade_id
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

        dispute.is_closed = True

        if dispute.dispute_result_property.value is not None:
            logger.warning(
                f"We already got a dispute result. That should only happen if a dispute needs to be closed "
                f"again because the first close did not succeed. TradeId = {trade_id}"
            )

        dispute.dispute_result_property.value = dispute_result
        trade_optional = self.trade_manager.get_trade_by_id(trade_id)
        error_message = None
        success = False

        try:
            # We need to avoid publishing the tx from both traders as it would create problems with zero confirmation withdrawals
            # There would be different transactions if both sign and publish (signers: once buyer+arb, once seller+arb)
            # The tx publisher is the winner or in case both get 50% the buyer, as the buyer has more inventive to publish the tx as he receives
            # more BTC as he has deposited
            contract = dispute.contract
            
            is_buyer = self.pub_key_ring == contract.buyer_pub_key_ring
            publisher = dispute_result.winner

            # Sometimes the user who receives the trade amount is never online, so we might want to
            # let the loser publish the tx. When the winner comes online he gets his funds as it was published by the other peer.
            # Default isLoserPublisher is set to false
            if dispute_result.is_loser_publisher:
                # we invert the logic
                if publisher == DisputeResultWinner.BUYER:
                    publisher = DisputeResultWinner.SELLER
                elif publisher == DisputeResultWinner.SELLER:
                    publisher = DisputeResultWinner.BUYER

            if (is_buyer and publisher == DisputeResultWinner.BUYER) or (not is_buyer and publisher == DisputeResultWinner.SELLER):
                payout_tx: Optional["Transaction"] = None
                if trade_optional:
                    payout_tx = trade_optional.payout_tx
                else:
                    tradable_optional = self.closed_tradable_manager.get_tradable_by_id(trade_id)
                    if isinstance(tradable_optional, Trade):
                        payout_tx = tradable_optional.payout_tx

                if payout_tx is None:
                    if dispute.deposit_tx_serialized:
                        multi_sig_pub_key = (
                            contract.buyer_multi_sig_pub_key if is_buyer 
                            else contract.seller_multi_sig_pub_key
                        )
                        multi_sig_key_pair = self.btc_wallet_service.get_multi_sig_key_pair(
                            trade_id, multi_sig_pub_key
                        )
                        signed_disputed_payout_tx = self.trade_wallet_service.trader_sign_and_finalize_disputed_payout_tx(
                            dispute.deposit_tx_serialized,
                            dispute_result.arbitrator_signature,
                            dispute_result.buyer_payout_amount,
                            dispute_result.seller_payout_amount,
                            contract.buyer_payout_address_string,
                            contract.seller_payout_address_string,
                            multi_sig_key_pair,
                            contract.buyer_multi_sig_pub_key,
                            contract.seller_multi_sig_pub_key,
                            dispute_result.arbitrator_pub_key
                        )
                        committed_disputed_payout_tx = WalletService.maybe_add_network_tx_to_wallet(
                            signed_disputed_payout_tx,
                            self.btc_wallet_service.get_wallet()
                        )
                        
                        class TxCallback(TxBroadcasterCallback):
                            
                            def on_success(self_, transaction: "Transaction"):
                                # after successful publish we send peer the tx
                                dispute.dispute_payout_tx_id = transaction.get_tx_id()
                                self.send_peer_published_payout_tx_message(transaction, dispute, contract)
                                self.update_trade_or_open_offer_manager(trade_id)

                            def on_failure(self_, e: Exception):
                                logger.error(e)


                        self.trade_wallet_service.broadcast_tx(
                            committed_disputed_payout_tx,
                            TxCallback(),
                            15
                        )

                        success = True
                    else:
                        error_message = f"DepositTx is None. TradeId = {trade_id}"
                        logger.warning(error_message)
                        success = False
                else:
                    logger.warning(
                        "We already got a payout tx. That might be the case if the other peer "
                        f"did not get the payout tx and opened a dispute. TradeId = {trade_id}"
                    )
                    dispute.dispute_payout_tx_id = payout_tx.get_tx_id()
                    self.send_peer_published_payout_tx_message(payout_tx, dispute, contract)
                    success = True
            else:
                logger.trace("We don't publish the tx as we are not the winning party.")
                # Clean up tangling trades
                if dispute.dispute_result_property.value is not None and dispute.is_closed:
                    self.update_trade_or_open_offer_manager(trade_id)
                success = True
        except TransactionVerificationException as e:
            error_message = f"Error at trader_sign_and_finalize_disputed_payout_tx: {e}"
            logger.error(error_message, exc_info=e)
            success = False
            
            # We prefer to close the dispute in that case. If there was no deposit tx and a random tx was used
            # we get a TransactionVerificationException. No reason to keep that dispute open...
            self.update_trade_or_open_offer_manager(trade_id)
            
            raise RuntimeError(error_message) 
        except (AddressFormatException, WalletException, SignatureDecodeException) as e:
            error_message = f"Error at trader_sign_and_finalize_disputed_payout_tx: {e}"
            logger.error(error_message, exc_info=e)
            success = False
            raise RuntimeError(error_message)
        finally:
            #    We use the chatMessage as we only persist those not the disputeResultMessage.
            # If we would use the disputeResultMessage we could not lookup for the msg when we receive the AckMessage.
            self.send_ack_message(chat_message, dispute.agent_pub_key_ring, success, error_message)

        self.maybe_clear_sensitive_data()
        self.request_persistence()

    # Losing trader or in case of 50/50 the seller gets the tx sent from the winner or buyer
    def on_disputed_payout_tx_message(
        self, peer_published_payout_tx_message: "PeerPublishedDisputePayoutTxMessage"
    ) -> None:
        uid = peer_published_payout_tx_message.uid
        trade_id = peer_published_payout_tx_message.trade_id
        dispute = self.find_own_dispute(trade_id)
        if dispute is None:
            logger.debug(
                f"We got a peerPublishedPayoutTxMessage but we don't have a matching dispute. TradeId = {trade_id}"
            )
            if uid not in self.delay_msg_map:
                # We delay 3 sec. to be sure the close msg gets added first
                timer = UserThread.run_after(
                    lambda: self.on_disputed_payout_tx_message(
                        peer_published_payout_tx_message
                    ),
                    timedelta(seconds=3),
                )
                self.delay_msg_map[uid] = timer
            else:
                logger.warning(
                    f"We got a peerPublishedPayoutTxMessage after we already repeated to apply the message after a delay. "
                    f"That should never happen. TradeId = {trade_id}"
                )
            return

        contract = dispute.contract
        is_buyer = self.pub_key_ring == contract.buyer_pub_key_ring
        peers_pub_key_ring = (
            contract.seller_pub_key_ring if is_buyer else contract.buyer_pub_key_ring
        )

        self.cleanup_retry_map(uid)

        committed_dispute_payout_tx = (
            WalletService.maybe_add_network_tx_to_wallet(
                peer_published_payout_tx_message.transaction,
                self.btc_wallet_service.get_wallet(),
            )
        )

        dispute.dispute_payout_tx_id = committed_dispute_payout_tx.get_tx_id()
        self.btc_wallet_service.print_tx(
            "Disputed payoutTx received from peer", committed_dispute_payout_tx
        )

        # We can only send the ack msg if we have the peers_pub_key_ring which requires the dispute
        self.send_ack_message(
            peer_published_payout_tx_message, peers_pub_key_ring, True, None
        )
        self.request_persistence()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Send messages
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # winner (or buyer in case of 50/50) sends tx to other peer
    def send_peer_published_payout_tx_message(
        self, transaction: "Transaction", dispute: "Dispute", contract: "Contract"
    ):
        peers_pub_key_ring = (
            contract.seller_pub_key_ring
            if dispute.dispute_opener_is_buyer
            else contract.buyer_pub_key_ring
        )
        peers_node_address = (
            contract.seller_node_address
            if dispute.dispute_opener_is_buyer
            else contract.buyer_node_address
        )

        logger.trace(
            f"sendPeerPublishedPayoutTxMessage to peerAddress {peers_node_address}"
        )

        message = PeerPublishedDisputePayoutTxMessage(
            transaction=transaction.serialize(),
            trade_id=dispute.trade_id,
            sender_node_address=self.p2p_service.get_address(),
            uid=str(uuid.uuid4()),
            support_type=self.get_support_type(),
        )

        logger.info(
            f"Send {message.__class__.__name__} to peer {peers_node_address}. "
            f"tradeId={message.trade_id}, uid={message.uid}"
        )

        class Listener(SendMailboxMessageListener):
            def on_arrived(self):
                logger.info(
                    f"{message.__class__.__name__} arrived at peer {peers_node_address}. "
                    f"tradeId={message.trade_id}, uid={message.uid}"
                )

            def on_stored_in_mailbox(self):
                logger.info(
                    f"{message.__class__.__name__} stored in mailbox for peer {peers_node_address}. "
                    f"tradeId={message.trade_id}, uid={message.uid}"
                )

            def on_fault(self, error_message):
                logger.error(
                    f"{message.__class__.__name__} failed: Peer {peers_node_address}. "
                    f"tradeId={message.trade_id}, uid={message.uid}, errorMessage={error_message}"
                )

        self.mailbox_message_service.send_encrypted_mailbox_message(
            peers_node_address, peers_pub_key_ring, message, Listener()
        )

    def update_trade_or_open_offer_manager(self, trade_id: str) -> None:
        # Set state after payout as we call swap_trade_entry_to_available_entry
        trade = self.trade_manager.get_trade_by_id(trade_id)
        if trade:
            self.trade_manager.close_disputed_trade(
                trade_id, TradeDisputeState.DISPUTE_CLOSED
            )
        else:
            open_offer = self.open_offer_manager.get_open_offer_by_id(trade_id)
            if open_offer:
                self.open_offer_manager.close_open_offer(open_offer.offer)
