from datetime import timedelta
from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING, List, Callable, Optional
from utils.preconditions import check_argument
from bisq.common.version import Version
from bisq.common.capabilities import Capabilities
from bisq.common.capability import Capability
from bisq.common.handlers.error_message_handler import ErrorMessageHandler
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.timer import Timer
from bisq.common.user_thread import UserThread
from bisq.core.exceptions.trade_price_out_of_tolerance_exception import (
    TradePriceOutOfToleranceException,
)
from bisq.core.locale.res import Res
from bisq.core.network.p2p.ack_message import AckMessage
from bisq.core.network.p2p.ack_message_source_type import AckMessageSourceType
from bisq.core.network.p2p.bootstrap_listener import BootstrapListener
from bisq.core.network.p2p.decrypted_message_with_pub_key import (
    DecryptedMessageWithPubKey,
)
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.network.p2p.send_direct_message_listener import SendDirectMessageListener
from bisq.core.network.utils.utils import Utils
from bisq.core.offer.availability.availability_result import AvailabilityResult
from bisq.core.offer.availability.dispute_agent_selection import DisputeAgentSelection
from bisq.core.offer.availability.messages.offer_availability_request import (
    OfferAvailabilityRequest,
)
from bisq.core.offer.availability.messages.offer_availability_response import (
    OfferAvailabilityResponse,
)
from bisq.core.offer.bisq_v1.market_price_not_available_exception import (
    MarketPriceNotAvailableException,
)
from bisq.core.offer.bisq_v1.offer_payload import OfferPayload
from bisq.core.offer.offer import Offer
from bisq.core.offer.offer_restrictions import OfferRestrictions
from bisq.core.offer.offer_state import OfferState
from bisq.core.offer.offer_util import OfferUtil
from bisq.core.offer.open_offer_state import OpenOfferState
from bisq.core.offer.placeoffer.bisq_v1.place_offer_model import PlaceOfferModel
from bisq.core.offer.placeoffer.bisq_v1.place_offer_protocol import PlaceOfferProtocol
from bisq.core.provider.mempool.fee_validation_status import FeeValidationStatus
from bisq.core.trade.bisq_v1.transaction_result_handler import TransactionResultHandler
from bisq.core.util.validator import Validator
from utils.data import ObservableList
from bisq.core.network.p2p.peers.peer_manager import PeerManager
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.core.network.p2p.decrypted_direct_message_listener import (
    DecryptedDirectMessageListener,
)
from bisq.core.trade.model.tradable_list import TradableList
from bisq.core.offer.open_offer import OpenOffer

if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bisq.core.offer.offer_book_service import OfferBookService
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.common.persistence.persistence_manager import PersistenceManager
    from bisq.core.api.core_context import CoreContext
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.btc.wallet.trade_wallet_service import TradeWalletService
    from bisq.core.dao.burningman.btc_fee_receiver_service import BtcFeeReceiverService
    from bisq.core.dao.burningman.delayed_payout_tx_receiver_service import (
        DelayedPayoutTxReceiverService,
    )
    from bisq.core.dao.dao_facade import DaoFacade
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.network.p2p.peers.broadcaster import Broadcaster
    from bisq.core.offer.bisq_v1.create_offer_service import CreateOfferService
    from bisq.core.provider.price.price_feed_service import PriceFeedService
    from bisq.core.support.dispute.arbitration.arbitrator.arbitrator_manager import (
        ArbitratorManager,
    )
    from bisq.core.support.dispute.mediation.mediator.mediator_manager import (
        MediatorManager,
    )
    from bisq.core.support.refund.refundagent.refund_agent_manager import (
        RefundAgentManager,
    )
    from bisq.core.trade.closed_tradable_manager import ClosedTradableManager
    from bisq.core.trade.statistics.trade_statistics_manager import (
        TradeStatisticsManager,
    )
    from bisq.core.user.preferences import Preferences
    from bisq.core.user.user import User


class OpenOfferManager(
    PeerManager.Listener,
    DecryptedDirectMessageListener,
    PersistedDataHost,
    DaoStateListener,
):
    RETRY_REPUBLISH_DELAY_SEC = 10
    REPUBLISH_AGAIN_AT_STARTUP_DELAY_SEC = 30
    REPUBLISH_INTERVAL_MS = int(timedelta(minutes=40).total_seconds() * 1000)
    REFRESH_INTERVAL_MS = int(timedelta(minutes=6).total_seconds() * 1000)

    def __init__(
        self,
        core_context: "CoreContext",
        create_offer_service: "CreateOfferService",
        key_ring: "KeyRing",
        user: "User",
        p2p_service: "P2PService",
        btc_wallet_service: "BtcWalletService",
        trade_wallet_service: "TradeWalletService",
        bsq_wallet_service: "BsqWalletService",
        offer_book_service: "OfferBookService",
        closed_tradable_manager: "ClosedTradableManager",
        price_feed_service: "PriceFeedService",
        preferences: "Preferences",
        trade_statistics_manager: "TradeStatisticsManager",
        arbitrator_manager: "ArbitratorManager",
        mediator_manager: "MediatorManager",
        refund_agent_manager: "RefundAgentManager",
        dao_facade: "DaoFacade",
        filter_manager: "FilterManager",
        btc_fee_receiver_service: "BtcFeeReceiverService",
        delayed_payout_tx_receiver_service: "DelayedPayoutTxReceiverService",
        broadcaster: "Broadcaster",
        persistence_manager: "PersistenceManager[TradableList[OpenOffer]]",
        dao_state_service: "DaoStateService",
    ):
        self.logger = get_ctx_logger(__name__)
        self.core_context = core_context
        self.create_offer_service = create_offer_service
        self.key_ring = key_ring
        self.user = user
        self.p2p_service = p2p_service
        self.btc_wallet_service = btc_wallet_service
        self.trade_wallet_service = trade_wallet_service
        self.bsq_wallet_service = bsq_wallet_service
        self.offer_book_service = offer_book_service
        self.closed_tradable_manager = closed_tradable_manager
        self.price_feed_service = price_feed_service
        self.preferences = preferences
        self.trade_statistics_manager = trade_statistics_manager
        self.arbitrator_manager = arbitrator_manager
        self.mediator_manager = mediator_manager
        self.refund_agent_manager = refund_agent_manager
        self.dao_facade = dao_facade
        self.filter_manager = filter_manager
        self.btc_fee_receiver_service = btc_fee_receiver_service
        self.delayed_payout_tx_receiver_service = delayed_payout_tx_receiver_service
        self.broadcaster = broadcaster
        self.persistence_manager = persistence_manager
        self.dao_state_service = dao_state_service

        self.offers_to_be_edited: dict[str, "OpenOffer"] = {}
        self.open_offers = TradableList["OpenOffer"]()
        self.stopped = False
        self.periodic_republish_offers_timer: Optional["Timer"] = None
        self.periodic_refresh_offers_timer: Optional["Timer"] = None
        self.retry_republish_offers_timer: Optional["Timer"] = None
        self.chain_not_synced_handler: Optional[Callable[[str], None]] = None
        self.invalid_offers = ObservableList[tuple["OpenOffer", str]]()
        self._subscriptions: list[Callable[[], None]] = []

        self.persistence_manager.initialize(
            self.open_offers, PersistenceManagerSource.PRIVATE, "OpenOffers"
        )

    def read_persisted(self, complete_handler: Callable[[], None]):
        def on_persisted(persisted: "TradableList[OpenOffer]"):
            self.open_offers.set_all(persisted.list)
            for open_offer in self.open_offers:
                open_offer.get_offer().price_feed_service = self.price_feed_service
            complete_handler()

        self.persistence_manager.read_persisted(on_persisted, complete_handler)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_parse_block_complete_after_batch_processing(self, block):
        invalid_offer_ids = {
            invalid_offer[0].get_id() for invalid_offer in self.invalid_offers
        }
        exceeding_offers = [
            (
                open_offer,
                self._create_trade_limit_exceeded_message(open_offer.get_offer()),
            )
            for open_offer in self.open_offers
            if open_offer.get_id() not in invalid_offer_ids
            and OfferUtil.does_offer_amount_exceed_trade_limit(open_offer.get_offer())
        ]
        self.invalid_offers.extend(exceeding_offers)

    def _create_trade_limit_exceeded_message(self, offer: "Offer"):
        return (
            f"Your offer with ID `{offer.short_id}` has become invalid because the max. allowed trade amount has been changed.\n\n"
            f"The new trade limit has been activated by DAO voting. See https://github.com/bisq-network/proposals/issues/453 for more details.\n\n"
            f"You can request a reimbursement from the Bisq DAO for the lost `maker-fee` at: https://github.com/bisq-network/support/issues.\n"
            f"If you have any questions please reach out to the Bisq community at: https://bisq.network/community."
        )

    def on_all_services_initialized(self):
        self._subscriptions.append(
            self.p2p_service.add_decrypted_direct_message_listener(self)
        )
        self._subscriptions.append(self.dao_state_service.add_dao_state_listener(self))

        if self.p2p_service.is_bootstrapped:
            self.on_bootstrap_complete()
        else:

            class Listener(BootstrapListener):
                def on_data_received(self_):
                    self.on_bootstrap_complete()

            self._subscriptions.append(
                self.p2p_service.add_p2p_service_listener(Listener())
            )

        self.clean_up_address_entries()

        for open_offer in self.open_offers:
            error_msg = OfferUtil.get_invalid_maker_fee_tx_error_message(
                open_offer.get_offer(), self.btc_wallet_service
            )
            if error_msg:
                self.invalid_offers.append((open_offer, error_msg))

    def clean_up_address_entries(self):
        open_offers_id_set = {open_offer.get_id() for open_offer in self.open_offers}

        # We reset all AddressEntriesForOpenOffer which do not have a corresponding openOffer
        for entry in self.btc_wallet_service.get_address_entries_for_open_offer():
            if entry.offer_id not in open_offers_id_set:
                self.logger.warning(
                    f"We found an outdated addressEntry for openOffer {entry.offer_id} "
                    f"(openOffers does not contain that offer), offers.size={len(self.open_offers)}"
                )
                self.btc_wallet_service.reset_address_entries_for_open_offer(
                    entry.offer_id
                )

    def shut_down(self, complete_handler: Optional[Callable[[], None]] = None):
        self.stopped = True
        for unsub in self._subscriptions:
            unsub()
        self._subscriptions.clear()

        self.stop_periodic_refresh_offers_timer()
        self.stop_periodic_republish_offers_timer()
        self.stop_retry_republish_offers_timer()

        self.delayed_payout_tx_receiver_service.shut_down()
        self.btc_fee_receiver_service.shut_down()

        # we remove own offers from offerbook when we go offline
        # Normally we use a delay for broadcasting to the peers, but at shut down we want to get it fast out
        size = len(self.open_offers)
        self.logger.info(
            f"Remove open offers at shutDown. Number of open offers: {size}"
        )
        if self.offer_book_service.is_bootstrapped and size > 0:

            def execute():
                for open_offer in self.open_offers:
                    self.offer_book_service.remove_offer_at_shut_down(
                        open_offer.get_offer().offer_payload_base
                    )
                self.offer_book_service.shut_down()

            UserThread.execute(execute)

            # Force broadcaster to send out immediately, otherwise we could have a 2 sec delay until the
            # bundled messages sent out.
            self.broadcaster.flush()

            if complete_handler:
                # For typical number of offers we are tolerant with delay to give enough time to broadcast.
                # If number of offers is very high we limit to 3 sec. to not delay other shutdown routines.
                delay = min(3000, size * 200 + 500)
                UserThread.run_after(complete_handler, timedelta(milliseconds=delay))
        elif complete_handler:
            complete_handler()

    def remove_all_open_offers(
        self, complete_handler: Optional[Callable[[], None]] = None
    ):
        self.remove_open_offers(self.get_observable_list(), complete_handler)

    def remove_open_offers(
        self,
        open_offers: List["OpenOffer"],
        complete_handler: Optional[Callable[[], None]] = None,
    ):
        size = len(open_offers)
        # Copy list as we remove in the loop
        open_offers_list = open_offers.copy()
        for offer in open_offers_list:
            self.remove_open_offer(offer)

        if complete_handler:
            delay = size * 200 + 500
            UserThread.run_after(complete_handler, timedelta(milliseconds=delay))

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DecryptedDirectMessageListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_direct_message(
        self,
        decrypted_message_with_pub_key: "DecryptedMessageWithPubKey",
        peer_node_address: "NodeAddress",
    ):
        # Handler for incoming offer availability requests
        # We get an encrypted message but don't do the signature check as we don't know the peer yet.
        # A basic sig check is done also at decryption time
        network_envelope = decrypted_message_with_pub_key.network_envelope

        if isinstance(network_envelope, OfferAvailabilityRequest):
            self.handle_offer_availability_request(network_envelope, peer_node_address)
        elif isinstance(network_envelope, AckMessage):
            ack_message = network_envelope
            if ack_message.source_type == AckMessageSourceType.OFFER_MESSAGE:
                if ack_message.success:
                    self.logger.info(
                        f"Received AckMessage for {ack_message.source_msg_class_name} with offerId {ack_message.source_id} and uid {ack_message.source_uid}"
                    )
                else:
                    self.logger.warning(
                        f"Received AckMessage with error state for {ack_message.source_msg_class_name} with offerId {ack_message.source_id} and errorMessage={ack_message.error_message}"
                    )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // BootstrapListener delegate
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_bootstrap_complete(self):
        self.stopped = False

        self.maybe_update_persisted_offers()

        # Republish means we send the complete offer object
        self.republish_offers()
        self.start_periodic_republish_offers_timer()

        # Refresh is started once we get a success from republish

        # We republish after a bit as it might be that our connected node still has the offer in the data map
        # but other peers have it already removed because of expired TTL.
        # Those other not directly connected peers would not get the broadcast of the new offer, as the first
        # connected peer (seed node) does not broadcast if it has the data in the map.
        # To update quickly to the whole network we repeat the republish_offers call after a few seconds when we
        # are better connected to the network. There is no guarantee that all peers will receive it but we also
        # have our periodic timer, so after that longer interval the offer should be available to all peers.
        if self.retry_republish_offers_timer is None:
            self.retry_republish_offers_timer = UserThread.run_after(
                self.republish_offers,
                timedelta(
                    seconds=OpenOfferManager.REPUBLISH_AGAIN_AT_STARTUP_DELAY_SEC
                ),
            )

        self._subscriptions.append(self.p2p_service.peer_manager.add_listener(self))

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PeerManager.Listener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_all_connections_lost(self):
        self.logger.info("onAllConnectionsLost")
        self.stopped = True
        self.stop_periodic_refresh_offers_timer()
        self.stop_periodic_republish_offers_timer()
        self.stop_retry_republish_offers_timer()

        self.restart()

    def on_new_connection_after_all_connections_lost(self):
        self.logger.info("onNewConnectionAfterAllConnectionsLost")
        self.stopped = False
        self.restart()

    def on_awake_from_standby(self):
        self.logger.info("onAwakeFromStandby")
        self.stopped = False
        if self.p2p_service.network_node.get_all_connections():
            self.restart()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def place_offer(
        self,
        offer: "Offer",
        buyer_security_deposit: float,
        use_savings_wallet: bool,
        is_shared_maker_fee: bool,
        trigger_price: int,
        result_handler: TransactionResultHandler,
        error_message_handler: ErrorMessageHandler,
    ):
        assert offer.maker_fee is not None, "maker_fee must not be none"
        check_argument(
            not offer.is_bsq_swap_offer, "Offer must not be a BSQ swap offer"
        )

        num_clones = len(
            self.get_open_offers_by_maker_fee_tx_id(offer.offer_fee_payment_tx_id)
        )
        if num_clones >= 10:
            error_message_handler(
                "Cannot create offer because maximum number of 10 cloned offers with shared maker fee is reached."
            )
            return

        reserved_funds_for_offer = (
            self.create_offer_service.get_reserved_funds_for_offer(
                offer.direction,
                offer.amount,
                buyer_security_deposit,
                self.create_offer_service.get_seller_security_deposit_as_float(
                    buyer_security_deposit
                ),
            )
        )

        model = PlaceOfferModel(
            offer=offer,
            reserved_funds_for_offer=reserved_funds_for_offer,
            use_savings_wallet=use_savings_wallet,
            is_shared_maker_fee=is_shared_maker_fee,
            wallet_service=self.btc_wallet_service,
            trade_wallet_service=self.trade_wallet_service,
            bsq_wallet_service=self.bsq_wallet_service,
            offer_book_service=self.offer_book_service,
            arbitrator_manager=self.arbitrator_manager,
            trade_statistics_manager=self.trade_statistics_manager,
            dao_facade=self.dao_facade,
            btc_fee_receiver_service=self.btc_fee_receiver_service,
            user=self.user,
            filter_manager=self.filter_manager,
        )

        def on_transaction(transaction: "Transaction"):
            open_offer = OpenOffer(offer, trigger_price)
            if is_shared_maker_fee:
                if self.cannot_activate_offer(offer):
                    open_offer.state = OpenOfferState.DEACTIVATED
                else:

                    def on_success():
                        model.offer_added_to_offer_book = True

                    def on_error(error_message):
                        model.offer.error_message = (
                            "Could not add offer to offerbook.\n"
                            "Please check your network connection and try again."
                        )

                    # We did not use the AddToOfferBook task for publishing because we
                    # do not have created the openOffer during the protocol and we need that to determine if the offer can be activated.
                    # So in case we have an activated cloned offer we do the publishing here.
                    model.offer_book_service.add_offer(
                        model.offer, on_success, on_error
                    )

            self.add_open_offer_to_list(open_offer)
            if not self.stopped:
                self.start_periodic_republish_offers_timer()
                self.start_periodic_refresh_offers_timer()
            else:
                self.logger.debug(
                    "We have stopped already. We ignore that place_offer_protocol.place_offer.on_result call."
                )
            result_handler(transaction)

        place_offer_protocol = PlaceOfferProtocol(
            model, on_transaction, error_message_handler
        )
        place_offer_protocol.place_offer()

    def add_open_bsq_swap_offer(self, open_offer: "OpenOffer"):
        self.add_open_offer_to_list(open_offer)
        if not self.stopped:
            self.start_periodic_republish_offers_timer()
            self.start_periodic_refresh_offers_timer()
        else:
            self.logger.debug(
                "We have stopped already. We ignore that place_offer_protocol.place_offer.on_result call."
            )

    # Remove from offerbook
    def remove_offer(
        self,
        offer: "Offer",
        result_handler: Callable[[], None],
        error_message_handler: ErrorMessageHandler,
    ):
        open_offer_optional = self.get_open_offer_by_id(offer.id)
        if open_offer_optional:
            self.remove_open_offer(
                open_offer_optional, result_handler, error_message_handler
            )
        else:
            self.logger.warning(
                "Offer was not found in our list of open offers. We still try to remove it from the offerbook."
            )
            error_message_handler(
                "Offer was not found in our list of open offers. "
                "We still try to remove it from the offerbook."
            )

            def on_success():
                offer.state = OfferState.REMOVED

            self.offer_book_service.remove_offer(
                offer.offer_payload_base,
                on_success,
                None,
            )

    def activate_open_offer(
        self,
        open_offer: "OpenOffer",
        result_handler: Callable[[], None],
        error_message_handler: ErrorMessageHandler,
    ):
        if open_offer.get_id() in self.offers_to_be_edited:
            error_message_handler(
                Res.get("offerbook.cannotActivateEditedOffer.warning")
            )
            return

        if self.cannot_activate_offer(open_offer.get_offer()):
            error_message_handler(Res.get("offerbook.cannotActivate.warning"))
            return

        # If there is not enough funds for a BsqSwapOffer we do not publish the offer, but still apply the state change.
        # Once the wallet gets funded the offer gets published automatically.
        if self.is_bsq_swap_offer_lacking_funds(open_offer):
            open_offer.state = OpenOfferState.AVAILABLE
            self.request_persistence()
            result_handler()
            return

        offer = open_offer.get_offer()

        def on_success():
            open_offer.state = OpenOfferState.AVAILABLE
            open_offer.fee_validation_status = FeeValidationStatus.NOT_CHECKED_YET
            self.request_persistence()
            self.logger.debug(f"activate_open_offer, offer_id={offer.id}")
            result_handler()

        self.offer_book_service.activate_offer(offer, on_success, error_message_handler)

    def deactivate_open_offer(
        self,
        open_offer: "OpenOffer",
        result_handler: Callable[[], None],
        error_message_handler: ErrorMessageHandler,
    ):
        offer = open_offer.get_offer()

        def on_success():
            open_offer.state = OpenOfferState.DEACTIVATED
            self.request_persistence()
            self.logger.debug(f"deactivate_open_offer, offer_id={offer.id}")
            result_handler()

        self.offer_book_service.deactivate_offer(
            offer.offer_payload_base, on_success, error_message_handler
        )

    def remove_open_offer(
        self,
        open_offer: "OpenOffer",
        result_handler: Optional[Callable[[], None]] = None,
        error_message_handler: Optional[ErrorMessageHandler] = None,
    ):
        if not result_handler:
            result_handler = lambda: None
        if not error_message_handler:
            error_message_handler = lambda x: None

        if open_offer.get_id() not in self.offers_to_be_edited:
            offer = open_offer.get_offer()
            if open_offer.is_deactivated:
                self._on_removed(open_offer, result_handler, offer)
            else:
                self.offer_book_service.remove_offer(
                    offer.offer_payload_base,
                    lambda: self._on_removed(open_offer, result_handler, offer),
                    error_message_handler,
                )
        else:
            error_message_handler("You can't remove an offer that is currently edited.")

    def edit_open_offer_start(
        self,
        open_offer: "OpenOffer",
        result_handler: Callable[[], None],
        error_message_handler: ErrorMessageHandler,
    ):
        if open_offer.get_id() in self.offers_to_be_edited:
            self.logger.warning(
                "edit_open_offer_start called for an offer which is already in edit mode."
            )
            result_handler()
            return

        self.offers_to_be_edited[open_offer.get_id()] = open_offer

        if open_offer.is_deactivated:
            result_handler()
        else:

            def on_error(error_message):
                self.offers_to_be_edited.pop(open_offer.get_id(), None)
                error_message_handler(error_message)

            self.deactivate_open_offer(open_offer, result_handler, on_error)

    def edit_open_offer_publish(
        self,
        edited_offer: "Offer",
        trigger_price: int,
        original_state: "OpenOfferState",
        result_handler: Callable[[], None],
        error_message_handler: ErrorMessageHandler,
    ):
        open_offer = self.get_open_offer_by_id(edited_offer.id)

        if open_offer:

            open_offer.get_offer().state = OfferState.REMOVED
            open_offer.state = OpenOfferState.CANCELED
            self.remove_open_offer_from_list(open_offer)

            edited_open_offer = OpenOffer(edited_offer, trigger_price)
            edited_open_offer.state = original_state

            self.add_open_offer_to_list(edited_open_offer)

            if not edited_open_offer.is_deactivated:
                self.maybe_republish_offer(edited_open_offer)

            self.offers_to_be_edited.pop(open_offer.get_id(), None)
            result_handler()
        else:
            error_message_handler(
                "There is no offer with this id existing to be published."
            )

    def edit_open_offer_cancel(
        self,
        open_offer: "OpenOffer",
        original_state: "OpenOfferState",
        result_handler: Callable[[], None],
        error_message_handler: ErrorMessageHandler,
    ):
        if open_offer.get_id() in self.offers_to_be_edited:
            self.offers_to_be_edited.pop(open_offer.get_id(), None)
            if original_state == OpenOfferState.AVAILABLE:
                self.activate_open_offer(
                    open_offer, result_handler, error_message_handler
                )
            else:
                result_handler()

    def _on_removed(
        self,
        open_offer: "OpenOffer",
        result_handler: Callable[[], None],
        offer: "Offer",
    ):
        offer.state = OfferState.REMOVED
        open_offer.state = OpenOfferState.CANCELED
        self.remove_open_offer_from_list(open_offer)

        if not open_offer.get_offer().is_bsq_swap_offer:
            # For offers sharing maker fee with other offers, we only add to history
            # when the last offer with that maker fee txId is removed.
            # Only canceled offers which have lost maker fees are shown in history.
            # BSQ offers are not added for this reason.
            if not self.get_open_offers_by_maker_fee_tx_id(
                offer.offer_fee_payment_tx_id
            ):
                self.closed_tradable_manager.add(open_offer)

                # We only reset if there are no other offers with the shared maker fee as otherwise the
                # address in the addressEntry would become available while it's still RESERVED_FOR_TRADE
                # for the remaining offers.
                self.btc_wallet_service.reset_address_entries_for_open_offer(offer.id)

        self.logger.info(f"_on_removed offer_id={offer.id}")
        result_handler()

    # Close openOffer after deposit published
    def close_open_offer(self, offer: "Offer"):
        if offer.is_bsq_swap_offer:
            open_offer = self.get_open_offer_by_id(offer.id)
            if open_offer:
                self.remove_open_offer_from_list(open_offer)
                open_offer.state = OpenOfferState.CLOSED
                self.offer_book_service.remove_offer(
                    open_offer.get_offer().offer_payload_base,
                    lambda: self.logger.trace("Successfully removed offer"),
                    self.logger.error,
                )
        else:
            for open_offer in self.get_open_offers_by_maker_fee_tx_id(
                offer.offer_fee_payment_tx_id
            ):
                self.remove_open_offer_from_list(open_offer)

                if offer.id == open_offer.get_id():
                    open_offer.state = OpenOfferState.CLOSED
                else:
                    # We use CANCELED for the offers which have shared maker fee but have not been taken for the trade
                    open_offer.state = OpenOfferState.CANCELED
                    # We need to reset now those entries as well
                    self.btc_wallet_service.reset_address_entries_for_open_offer(
                        open_offer.get_id()
                    )

                self.offer_book_service.remove_offer(
                    open_offer.get_offer().offer_payload_base,
                    lambda: self.logger.trace("Successfully removed offer"),
                    self.logger.error,
                )

    def reserve_open_offer(self, open_offer: "OpenOffer"):
        open_offer.state = OpenOfferState.RESERVED
        self.request_persistence()

    def cannot_activate_offer(self, offer: "Offer") -> bool:
        return any(
            # Offers which share our maker fee will get checked if they have the same payment method
            # and currency.
            open_offer.get_offer().offer_fee_payment_tx_id is not None
            and open_offer.get_offer().offer_fee_payment_tx_id
            == offer.offer_fee_payment_tx_id
            and open_offer.get_offer().payment_method_id.lower()
            == offer.payment_method_id.lower()
            and open_offer.get_offer().counter_currency_code.lower()
            == offer.counter_currency_code.lower()
            and open_offer.get_offer().base_currency_code.lower()
            == offer.base_currency_code.lower()
            for open_offer in self.open_offers
            if (
                not open_offer.get_offer().is_bsq_swap_offer  # We only handle non-BSQ offers
                and open_offer.get_id() != offer.id  # our own offer gets skipped
                and not open_offer.is_deactivated  # we only check with activated offers
            )
        )

    def has_offer_shared_maker_fee(self, open_offer: "OpenOffer") -> bool:
        return (
            len(
                self.get_open_offers_by_maker_fee_tx_id(
                    open_offer.get_offer().offer_fee_payment_tx_id
                )
            )
            > 1
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getters
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def is_my_offer(self, offer: "Offer") -> bool:
        return offer.is_my_offer(self.key_ring)

    def get_observable_list(self) -> "ObservableList[OpenOffer]":
        return self.open_offers.get_observable_list()

    def get_open_offer_by_id(self, offer_id: str) -> Optional["OpenOffer"]:
        return next(
            (offer for offer in self.open_offers if offer.get_id() == offer_id), None
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // OfferPayload Availability
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def handle_offer_availability_request(
        self, request: "OfferAvailabilityRequest", peer_node_address: "NodeAddress"
    ):
        self.logger.info(
            f"Received OfferAvailabilityRequest from {peer_node_address} with "
            f"offerId {request.offer_id} and uid {request.uid}"
        )

        result = False
        error_message = None

        if OfferRestrictions.requires_node_address_update() and not Utils.is_v3_address(
            peer_node_address.host_name
        ):
            error_message = "We got a handle_offer_availability_request from a Tor node v2 address where a Tor node v3 address is required."
            self.logger.info(error_message)
            self._send_ack_message(request, peer_node_address, False, error_message)
            return

        if not self.p2p_service.is_bootstrapped:
            error_message = "We got a handle_offer_availability_request but we have not bootstrapped yet."
            self.logger.info(error_message)
            self._send_ack_message(request, peer_node_address, False, error_message)
            return

        # Don't allow trade start if BitcoinJ is not fully synced (bisq issue #4764)
        if not self.btc_wallet_service.is_chain_height_synced_within_tolerance:
            error_message = "We got a handle_offer_availability_request but our chain is not synced."
            self.logger.info(error_message)
            self._send_ack_message(request, peer_node_address, False, error_message)
            if self.chain_not_synced_handler:
                self.chain_not_synced_handler(Res.get("popup.warning.chainNotSynced"))
            return

        # Don't allow trade start if DAO is not fully synced
        if not self.dao_facade.is_dao_state_ready_and_in_sync:
            error_message = (
                "We got a handle_offer_availability_request but our DAO is not synced."
            )
            self.logger.info(error_message)
            self._send_ack_message(request, peer_node_address, False, error_message)
            if self.chain_not_synced_handler:
                self.chain_not_synced_handler(Res.get("popup.warning.daoNeedsResync"))
            return

        if self.stopped:
            error_message = "We have stopped already. We ignore that handle_offer_availability_request call."
            self.logger.debug(error_message)
            self._send_ack_message(request, peer_node_address, False, error_message)
            return

        try:
            Validator.non_empty_string_of(request.offer_id)
            assert request.pub_key_ring is not None, "pub_key_ring must not be None"
        except Exception as e:
            error_message = f"Message validation failed. Error={e}, Message={request}"
            self.logger.warning(error_message)
            self._send_ack_message(request, peer_node_address, False, error_message)
            return

        try:
            open_offer = self.get_open_offer_by_id(request.offer_id)
            availability_result: Optional["AvailabilityResult"] = None
            arbitrator_node_address: Optional["NodeAddress"] = None
            mediator_node_address: Optional["NodeAddress"] = None
            refund_agent_node_address: Optional["NodeAddress"] = None

            if open_offer:
                if not self._api_user_denied_by_offer(request):
                    if open_offer.state == OpenOfferState.AVAILABLE:
                        offer = open_offer.get_offer()
                        if not any(
                            addr == peer_node_address.get_full_address()
                            for addr in self.preferences.get_ignore_traders_list()
                        ):
                            mediator_node_address = (
                                DisputeAgentSelection.get_random_mediator(
                                    self.mediator_manager
                                ).node_address
                            )
                            open_offer.mediator_node_address = mediator_node_address

                            refund_agent_node_address = (
                                DisputeAgentSelection.get_random_refund_agent(
                                    self.refund_agent_manager
                                ).node_address
                            )
                            open_offer.refund_agent_node_address = (
                                refund_agent_node_address
                            )

                            try:
                                # Check also tradePrice to avoid failures after taker fee is paid caused by a too big difference
                                # in trade price between the peers. Also here poor connectivity might cause market price API connection
                                # losses and therefore an outdated market price.
                                offer.verify_takers_trade_price(
                                    request.takers_trade_price
                                )
                                availability_result = AvailabilityResult.AVAILABLE
                            except TradePriceOutOfToleranceException as e:
                                self.logger.warning(
                                    "Trade price check failed because takers price is outside out tolerance."
                                )
                                availability_result = (
                                    AvailabilityResult.PRICE_OUT_OF_TOLERANCE
                                )
                            except MarketPriceNotAvailableException as e:
                                self.logger.warning(e)
                                availability_result = (
                                    AvailabilityResult.MARKET_PRICE_NOT_AVAILABLE
                                )
                            except Exception as e:
                                self.logger.warning(f"Trade price check failed: {e}")
                                availability_result = (
                                    AvailabilityResult.PRICE_CHECK_FAILED
                                )
                        else:
                            availability_result = AvailabilityResult.USER_IGNORED
                    else:
                        availability_result = AvailabilityResult.OFFER_TAKEN
                else:
                    availability_result = AvailabilityResult.MAKER_DENIED_API_USER
            else:
                self.logger.warning(
                    "handle_offer_availability_request: openOffer not found."
                )
                availability_result = AvailabilityResult.OFFER_TAKEN

            if (
                self.btc_wallet_service.is_unconfirmed_transactions_limit_hit()
                or self.bsq_wallet_service.is_unconfirmed_transactions_limit_hit()
            ):
                error_message = Res.get("shared.unconfirmedTransactionsLimitReached")
                self.logger.warning(error_message)
                availability_result = AvailabilityResult.UNCONF_TX_LIMIT_HIT

            try:
                takers_burning_man_selection_height = (
                    request.burning_man_selection_height
                )
                check_argument(
                    takers_burning_man_selection_height > 0,
                    "takersBurningManSelectionHeight must not be 0",
                )

                makers_burning_man_selection_height = (
                    self.delayed_payout_tx_receiver_service.get_burning_man_selection_height()
                )
                check_argument(
                    takers_burning_man_selection_height
                    == makers_burning_man_selection_height,
                    "takersBurningManSelectionHeight does not match makersBurningManSelectionHeight. "
                    f"takersBurningManSelectionHeight={takers_burning_man_selection_height}; makersBurningManSelectionHeight={makers_burning_man_selection_height}",
                )
            except Exception as e:
                error_message = (
                    f"Message validation failed. Error={e}, Message={request}"
                )
                self.logger.warning(error_message)
                availability_result = AvailabilityResult.INVALID_SNAPSHOT_HEIGHT

            response = OfferAvailabilityResponse(
                offer_id=request.offer_id,
                availability_result=availability_result,
                arbitrator=arbitrator_node_address,
                mediator=mediator_node_address,
                refund_agent=refund_agent_node_address,
            )

            self.logger.info(
                f"Send {response.__class__.__name__} with offerId {response.offer_id} and uid {response.uid} to peer {peer_node_address}"
            )

            class Listener(SendDirectMessageListener):
                def on_arrived(self_):
                    self.logger.info(
                        f"{response.__class__.__name__} arrived at peer: offerId={response.offer_id}; uid={response.uid}"
                    )

                def on_fault(self_, error_msg: str):
                    self.logger.error(
                        f"Sending {response.__class__.__name__} failed: uid={response.uid}; peer={peer_node_address}; error={error_msg}"
                    )

            self.p2p_service.send_encrypted_direct_message(
                peer_node_address, request.pub_key_ring, response, Listener()
            )
            result = True

        except Exception as e:
            error_message = f"Exception at handle_offer_availability_request: {e}"
            self.logger.error(error_message, exc_info=e)
        finally:
            self._send_ack_message(request, peer_node_address, result, error_message)

    def _api_user_denied_by_offer(self, request: "OfferAvailabilityRequest") -> bool:
        return self.preferences.is_deny_api_taker() and request.is_taker_api_user

    def _send_ack_message(
        self,
        message: "OfferAvailabilityRequest",
        sender: "NodeAddress",
        result: bool,
        error_message: Optional[str],
    ):
        offer_id = message.offer_id
        source_uid = message.uid
        ack_message = AckMessage(
            sender_node_address=self.p2p_service.network_node.node_address_property.value,
            source_type=AckMessageSourceType.OFFER_MESSAGE,
            source_msg_class_name=message.__class__.__name__,
            source_uid=source_uid,
            source_id=offer_id,
            success=result,
            error_message=error_message,
        )

        takers_node_address = sender
        takers_pub_key_ring = message.pub_key_ring
        self.logger.info(
            f"Send AckMessage for OfferAvailabilityRequest to peer {takers_node_address} "
            f"with offerId {offer_id} and sourceUid {ack_message.source_uid}"
        )

        class Listener(SendDirectMessageListener):
            def on_arrived(self_):
                self.logger.info(
                    f"AckMessage for OfferAvailabilityRequest arrived at takersNodeAddress "
                    f"{takers_node_address}. offerId={offer_id}, sourceUid={ack_message.source_uid}"
                )

            def on_fault(self_, error_message: str):
                self.logger.error(
                    f"AckMessage for OfferAvailabilityRequest failed. AckMessage={ack_message}, "
                    f"takersNodeAddress={takers_node_address}, errorMessage={error_message}"
                )

        self.p2p_service.send_encrypted_direct_message(
            takers_node_address, takers_pub_key_ring, ack_message, Listener()
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Update persisted offer if a new capability is required after a software update
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def maybe_update_persisted_offers(self):
        open_offers_clone = self.open_offers.list.copy()

        for original_open_offer in open_offers_clone:
            original_offer = original_open_offer.get_offer()
            if original_offer.is_bsq_swap_offer:
                # Offer without a fee transaction don't need to be updated, they can be removed and a new
                # offer created without incurring any extra costs
                continue

            original = original_offer.offer_payload
            if not original:
                continue

            # We added CAPABILITIES with entry for Capability.MEDIATION in v1.1.6 and
            # Capability.REFUND_AGENT in v1.2.0 and want to rewrite a
            # persisted offer after the user has updated to 1.2.0 so their offer will be accepted by the network.
            if (
                original.protocol_version < Version.TRADE_PROTOCOL_VERSION
                or not OfferRestrictions.has_offer_mandatory_capability(
                    original_offer, Capability.MEDIATION
                )
                or not OfferRestrictions.has_offer_mandatory_capability(
                    original_offer, Capability.REFUND_AGENT
                )
                or not original.owner_node_address == self.p2p_service.address
            ):

                # - Capabilities changed?
                # We rewrite our offer with the additional capabilities entry
                updated_extra_data_map = dict[str, str]()
                if not OfferRestrictions.has_offer_mandatory_capability(
                    original_offer, Capability.MEDIATION
                ) or not OfferRestrictions.has_offer_mandatory_capability(
                    original_offer, Capability.REFUND_AGENT
                ):
                    original_extra_data_map = original.extra_data_map

                    if original_extra_data_map is not None:
                        updated_extra_data_map.update(original_extra_data_map)

                    # We overwrite any entry with our current capabilities
                    updated_extra_data_map[OfferPayload.CAPABILITIES] = (
                        Capabilities.app.to_string_list()
                    )

                    self.logger.info(
                        f"Converted offer to support new Capability.MEDIATION and Capability.REFUND_AGENT capability. id={original_offer.id}"
                    )
                else:
                    updated_extra_data_map = original.extra_data_map

                # - Protocol version changed?
                protocol_version = original.protocol_version
                if protocol_version < Version.TRADE_PROTOCOL_VERSION:
                    # We update the trade protocol version
                    protocol_version = Version.TRADE_PROTOCOL_VERSION
                    self.logger.info(
                        f"Updated the protocol version of offer id={original_offer.id}"
                    )

                # - node address changed? (due to a faulty tor dir)
                owner_node_address = original.owner_node_address
                if owner_node_address != self.p2p_service.address:
                    owner_node_address = self.p2p_service.address
                    self.logger.info(
                        f"Updated the owner nodeaddress of offer id={original_offer.id}"
                    )

                updated_payload = OfferPayload(
                    id=original.id,
                    date=original.date,
                    owner_node_address=owner_node_address,
                    pub_key_ring=original.pub_key_ring,
                    direction=original.direction,
                    price=original.price,
                    market_price_margin=original.market_price_margin,
                    use_market_based_price=original.use_market_based_price,
                    amount=original.amount,
                    min_amount=original.min_amount,
                    base_currency_code=original.base_currency_code,
                    counter_currency_code=original.counter_currency_code,
                    arbitrator_node_addresses=original.arbitrator_node_addresses,
                    mediator_node_addresses=original.mediator_node_addresses,
                    payment_method_id=original.payment_method_id,
                    maker_payment_account_id=original.maker_payment_account_id,
                    offer_fee_payment_tx_id=original.offer_fee_payment_tx_id,
                    country_code=original.country_code,
                    accepted_country_codes=original.accepted_country_codes,
                    bank_id=original.bank_id,
                    accepted_bank_ids=original.accepted_bank_ids,
                    version_nr=original.version_nr,
                    block_height_at_offer_creation=original.block_height_at_offer_creation,
                    tx_fee=original.tx_fee,
                    maker_fee=original.maker_fee,
                    is_currency_for_maker_fee_btc=original.is_currency_for_maker_fee_btc,
                    buyer_security_deposit=original.buyer_security_deposit,
                    seller_security_deposit=original.seller_security_deposit,
                    max_trade_limit=original.max_trade_limit,
                    max_trade_period=original.max_trade_period,
                    use_auto_close=original.use_auto_close,
                    use_re_open_after_auto_close=original.use_re_open_after_auto_close,
                    lower_close_price=original.lower_close_price,
                    upper_close_price=original.upper_close_price,
                    is_private_offer=original.is_private_offer,
                    hash_of_challenge=original.hash_of_challenge,
                    extra_data_map=updated_extra_data_map,
                    protocol_version=protocol_version,
                )

                # Save states from original data to use for the updated
                original_offer_state = original_offer.state
                original_open_offer_state = original_open_offer.state

                # remove old offer
                original_offer.state = OfferState.REMOVED
                original_open_offer.state = OpenOfferState.CANCELED
                self.remove_open_offer_from_list(original_open_offer)

                # Create new Offer
                updated_offer = Offer(updated_payload)
                updated_offer.price_feed_service = self.price_feed_service
                updated_offer.state = original_offer_state

                updated_open_offer = OpenOffer(
                    updated_offer, original_open_offer.trigger_price
                )
                updated_open_offer.state = original_open_offer_state
                self.add_open_offer_to_list(updated_open_offer)

                self.logger.info(f"Updating offer completed. id={original_offer.id}")

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // RepublishOffers, refreshOffers
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def republish_offers(self):
        if self.stopped:
            return
        self.stop_periodic_refresh_offers_timer()

        # Convert to list to avoid concurrent modification
        open_offers_list = list(self.open_offers.list)
        self._process_list_for_republish_offers(open_offers_list)

    def _process_list_for_republish_offers(self, offers_list: list["OpenOffer"]):
        if not offers_list:
            return

        open_offer = offers_list.pop(0)
        if open_offer in self.open_offers:
            self.maybe_republish_offer(
                open_offer, lambda: self._process_list_for_republish_offers(offers_list)
            )
        else:
            # If the offer was removed in the meantime or if its deactivated we skip and call
            # _process_list_for_republish_offers again with the list where we removed the offer already
            self._process_list_for_republish_offers(offers_list)

    def maybe_republish_offer(
        self,
        open_offer: "OpenOffer",
        complete_handler: Optional[Callable[[], None]] = None,
    ):
        if self._prevented_from_publishing(open_offer):
            if complete_handler:
                complete_handler()
            return

        def on_success():
            if not self.stopped:
                # Refresh means we send only the data needed to refresh the TTL (hash, signature and sequence no.)
                if self.periodic_refresh_offers_timer is None:
                    self.start_periodic_refresh_offers_timer()
                if complete_handler:
                    complete_handler()

        def on_error(error_message: str):
            if not self.stopped:
                self.logger.error(
                    f"Adding offer to P2P network failed. {error_message}"
                )
                self.stop_retry_republish_offers_timer()
                self.retry_republish_offers_timer = UserThread.run_after(
                    self.republish_offers,
                    timedelta(seconds=OpenOfferManager.RETRY_REPUBLISH_DELAY_SEC),
                )
                if complete_handler:
                    complete_handler()

        self.offer_book_service.add_offer(open_offer.get_offer(), on_success, on_error)

    def start_periodic_republish_offers_timer(self):
        self.stopped = False
        if self.periodic_republish_offers_timer is None:
            self.periodic_republish_offers_timer = UserThread.run_periodically(
                lambda: self.republish_offers() if not self.stopped else None,
                timedelta(milliseconds=OpenOfferManager.REPUBLISH_INTERVAL_MS),
            )

    def start_periodic_refresh_offers_timer(self):
        self.stopped = False
        # refresh sufficiently before offer would expire
        if self.periodic_refresh_offers_timer is None:

            def refresh_action():
                if self.stopped:
                    self.logger.debug(
                        "We have stopped already. We ignore that periodic_refresh_offers_timer.run call."
                    )
                    return

                size = len(self.open_offers)
                # we clone our list as open_offers might change during our delayed call
                open_offers_list = self.open_offers.list.copy()

                for i in range(size):
                    # we delay to avoid reaching throttle limits
                    # roughly 4 offers per second
                    delay = 300
                    min_delay = (i + 1) * delay
                    max_delay = (i + 2) * delay
                    open_offer = open_offers_list[i]

                    def refresh_check(offer: "OpenOffer"):
                        # we need to check if in the meantime the offer has been removed
                        if offer in self.open_offers:
                            self.maybe_refresh_offer(offer)

                    UserThread.run_after_random_delay(
                        lambda o=open_offer: refresh_check(o),
                        timedelta(milliseconds=min_delay),
                        timedelta(milliseconds=max_delay),
                    )

            self.periodic_refresh_offers_timer = UserThread.run_periodically(
                refresh_action,
                timedelta(milliseconds=OpenOfferManager.REFRESH_INTERVAL_MS),
            )
        else:
            self.logger.trace("periodic_refresh_offers_timer already started")

    def maybe_refresh_offer(self, open_offer: "OpenOffer"):
        if self._prevented_from_publishing(open_offer):
            return

        def on_success():
            self.logger.debug("Successfully refreshed TTL for offer")

        def on_error(error_message):
            self.logger.warning(error_message)

        self.offer_book_service.refresh_ttl(
            open_offer.get_offer().offer_payload_base, on_success, on_error
        )

    def restart(self):
        self.logger.debug("Restart after connection loss")

        def republish():
            self.stopped = False
            self.stop_retry_republish_offers_timer()
            self.republish_offers()

        if self.retry_republish_offers_timer is None:
            self.retry_republish_offers_timer = UserThread.run_after(
                republish, timedelta(seconds=OpenOfferManager.RETRY_REPUBLISH_DELAY_SEC)
            )

        self.start_periodic_republish_offers_timer()

    def request_persistence(self):
        self.persistence_manager.request_persistence()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def stop_periodic_refresh_offers_timer(self):
        if self.periodic_refresh_offers_timer:
            self.periodic_refresh_offers_timer.stop()
            self.periodic_refresh_offers_timer = None

    def stop_periodic_republish_offers_timer(self):
        if self.periodic_republish_offers_timer:
            self.periodic_republish_offers_timer.stop()
            self.periodic_republish_offers_timer = None

    def stop_retry_republish_offers_timer(self):
        if self.retry_republish_offers_timer:
            self.retry_republish_offers_timer.stop()
            self.retry_republish_offers_timer = None

    def add_open_offer_to_list(self, open_offer: "OpenOffer"):
        self.open_offers.append(open_offer)
        self.request_persistence()

    def remove_open_offer_from_list(self, open_offer: "OpenOffer"):
        self.open_offers.remove(open_offer)
        self.request_persistence()

    def is_bsq_swap_offer_lacking_funds(self, open_offer: "OpenOffer") -> bool:
        return (
            open_offer.get_offer().is_bsq_swap_offer
            and open_offer.bsq_swap_offer_has_missing_funds
        )

    def _prevented_from_publishing(self, open_offer: "OpenOffer") -> bool:
        return (
            open_offer.is_deactivated
            or open_offer.bsq_swap_offer_has_missing_funds
            or self.cannot_activate_offer(open_offer.get_offer())
        )

    def get_open_offers_by_maker_fee_tx_id(
        self, maker_fee_tx_id: str
    ) -> set["OpenOffer"]:
        return {
            open_offer
            for open_offer in self.open_offers
            if (
                not open_offer.get_offer().is_bsq_swap_offer
                and maker_fee_tx_id is not None
                and maker_fee_tx_id == open_offer.get_offer().offer_fee_payment_tx_id
            )
        }
