from collections.abc import Callable
from concurrent.futures import Future
from datetime import timedelta
from typing import TYPE_CHECKING
from bisq.common.crypto.proof_of_work_service_instance_holder import (
    pow_service_for_version,
)
from bisq.common.handlers.error_message_handler import ErrorMessageHandler
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.monetary.price import Price
from bisq.core.offer.bsq_swap.bsq_swap_offer_payload import BsqSwapOfferPayload
from bisq.core.offer.offer_direction import OfferDirection
from bisq.core.offer.offer_state import OfferState
from bisq.core.offer.offer_util import OfferUtil
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.network.p2p.bootstrap_listener import BootstrapListener
from bisq.core.offer.placeoffer.bsq_swap.place_bsq_swap_offer_model import (
    PlaceBsqSwapOfferModel,
)
from bisq.core.offer.placeoffer.bsq_swap.place_bsq_swap_offer_protocol import (
    PlaceBsqSwapOfferProtocol,
)
from bisq.core.payment.payload.payment_method import PaymentMethod
from bitcoinj.base.coin import Coin
from utils.data import ObservableChangeEvent, SimplePropertyChangeEvent
from bisq.core.offer.bsq_swap.open_bsq_swap_offer import OpenBsqSwapOffer
from utils.preconditions import check_argument
from utils.time import get_time_ms
from bisq.common.version import Version
from bisq.core.offer.offer import Offer

if TYPE_CHECKING:
    from bisq.common.crypto.proof_of_work import ProofOfWork
    from bisq.common.crypto.proof_of_work_service import ProofOfWorkService
    from bisq.core.filter.filter import Filter
    from bisq.core.offer.open_offer import OpenOffer
    from bisq.common.crypto.pub_key_ring import PubKeyRing
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.dao.dao_facade import DaoFacade
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.offer.offer_book_service import OfferBookService
    from bisq.core.offer.open_offer_manager import OpenOfferManager
    from bisq.core.provider.fee.fee_service import FeeService


logger = get_logger(__name__)

class OpenBsqSwapOfferService:
    def __init__(
        self,
        open_offer_manager: "OpenOfferManager",
        btc_wallet_service: "BtcWalletService",
        bsq_wallet_service: "BsqWalletService",
        fee_service: "FeeService",
        p2p_service: "P2PService",
        dao_facade: "DaoFacade",
        offer_book_service: "OfferBookService",
        offer_util: "OfferUtil",
        filter_manager: "FilterManager",
        pub_key_ring: "PubKeyRing",
    ):
        self.open_offer_manager = open_offer_manager
        self.btc_wallet_service = btc_wallet_service
        self.bsq_wallet_service = bsq_wallet_service
        self.fee_service = fee_service
        self.p2p_service = p2p_service
        self.dao_facade = dao_facade
        self.offer_book_service = offer_book_service
        self.offer_util = offer_util
        self.filter_manager = filter_manager
        self.pub_key_ring = pub_key_ring

        self.open_bsq_swap_offers_by_id = dict[str, "OpenBsqSwapOffer"]()

        def _on_offer_list_change(e: ObservableChangeEvent["OpenOffer"]):
            if e.added_elements:
                self._on_open_offers_added(e.added_elements)
            if e.removed_elements:
                self._on_open_offers_removed(e.removed_elements)

        self.offer_list_change_listener = _on_offer_list_change

        class BootstrapListenerImpl(BootstrapListener):
            def on_data_received(self_):
                self._on_p2p_service_ready()
                self.p2p_service.remove_p2p_service_listener(self.bootstrap_listener)

        self.bootstrap_listener = BootstrapListenerImpl()

        class DaoStateListenerImpl(DaoStateListener):
            def on_parse_block_complete_after_batch_processing(self_, block):
                # The balance gets updated at the same event handler but we do not know which handler
                # gets called first, so we delay here a bit to be sure the balance is set
                UserThread.run_after(
                    lambda: [
                        self._on_dao_ready(),
                        self.dao_facade.remove_bsq_state_listener(
                            self.dao_state_listener
                        ),
                    ],
                    timedelta(milliseconds=100),
                )

        self.dao_state_listener = DaoStateListenerImpl()

        def _on_filter_changed(e: SimplePropertyChangeEvent["Filter"]):
            if e.new_value:
                self._on_proof_of_work_difficulty_changed()

        self.filter_change_listener = _on_filter_changed

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_all_services_initialized(self):
        if self.p2p_service.is_bootstrapped:
            self._on_p2p_service_ready()
        else:
            self.p2p_service.add_p2p_service_listener(self.bootstrap_listener)

    def _on_p2p_service_ready(self):
        if self.dao_facade.is_parse_block_chain_complete:
            self._on_dao_ready()
        else:
            self.dao_facade.add_bsq_state_listener(self.dao_state_listener)

    def _on_dao_ready(self):
        self.filter_manager.filter_property.add_listener(self.filter_change_listener)
        self.open_offer_manager.get_observable_list().add_listener(
            self.offer_list_change_listener
        )
        self._on_open_offers_added(self.open_offer_manager.get_observable_list())

    def shut_down(self):
        self.open_offer_manager.get_observable_list().remove_listener(
            self.offer_list_change_listener
        )
        self.p2p_service.remove_p2p_service_listener(self.bootstrap_listener)
        self.dao_facade.remove_bsq_state_listener(self.dao_state_listener)
        self.filter_manager.filter_property.remove_listener(self.filter_change_listener)

    def request_new_offer(
        self,
        offer_id: str,
        direction: "OfferDirection",
        amount: Coin,
        min_amount: Coin,
        price: Price,
        result_handler: Callable[["Offer"], None],
    ):
        logger.info(
            f"offer_id={offer_id},\n"
            f"direction={direction},\n"
            f"price={price.value},\n"
            f"amount={amount.value},\n"
            f"min_amount={min_amount.value}"
        )

        maker_address = self.p2p_service.address
        assert maker_address is not None
        self.offer_util.validate_basic_offer_data(PaymentMethod.BSQ_SWAP, "BSQ")

        difficulty = self._get_pow_difficulty()

        def on_pow_complete(f: Future["ProofOfWork"]):
            try:
                proof_of_work = f.result()

                def execute_on_user_thread():
                    bsq_swap_offer_payload = BsqSwapOfferPayload(
                        id=offer_id,
                        date=get_time_ms(),
                        owner_node_address=maker_address,
                        pub_key_ring=self.pub_key_ring,
                        direction=direction,
                        price=price.value,
                        amount=amount.value,
                        min_amount=min_amount.value,
                        proof_of_work=proof_of_work,
                        extra_data_map=None,
                        version_nr=Version.VERSION,
                        protocol_version=Version.TRADE_PROTOCOL_VERSION,
                    )
                    result_handler(Offer(bsq_swap_offer_payload))

                UserThread.execute(execute_on_user_thread)
            except Exception as e:
                logger.error(str(e))

        self._get_pow_service().mint_with_ids(
            offer_id,
            maker_address.get_full_address(),
            difficulty,
        ).add_done_callback(on_pow_complete)

    def place_bsq_swap_offer(
        self,
        offer: "Offer",
        result_handler: Callable[[], None],
        error_message_handler: ErrorMessageHandler,
    ):
        check_argument(offer.is_bsq_swap_offer, "Offer must be a BSQ swap offer")
        model = PlaceBsqSwapOfferModel(offer, self.offer_book_service)

        def on_complete():
            open_offer = OpenOffer(offer)
            self.open_offer_manager.add_open_bsq_swap_offer(open_offer)
            result_handler()

        protocol = PlaceBsqSwapOfferProtocol(model, on_complete, error_message_handler)
        protocol.place_offer()

    def activate_open_offer(
        self,
        open_offer: "OpenOffer",
        result_handler: Callable[[], None],
        error_message_handler: ErrorMessageHandler,
    ):
        if self._is_proof_of_work_invalid(open_offer.get_offer()):
            self._redo_proof_of_work_and_republish(open_offer)
            return

        self.open_offer_manager.activate_open_offer(
            open_offer,
            result_handler,
            error_message_handler,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Package scope
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def request_persistence(self):
        self.open_offer_manager.request_persistence()

    def enable_bsq_swap_offer(self, open_offer: "OpenOffer"):
        if self._is_proof_of_work_invalid(open_offer.get_offer()):
            self._redo_proof_of_work_and_republish(open_offer)
            return

        def on_success():
            open_offer.state = OfferState.AVAILABLE
            self.open_offer_manager.request_persistence()
            logger.info(f"enableBsqSwapOffer {open_offer.get_short_id()}")

        def on_error(error_msg):
            logger.warning(f"Failed to enableBsqSwapOffer {open_offer.get_short_id()}")

        self.offer_book_service.add_offer(open_offer.get_offer(), on_success, on_error)

    def disable_bsq_swap_offer(self, open_offer: "OpenOffer"):
        def on_success():
            logger.info(f"disableBsqSwapOffer {open_offer.get_short_id()}")

        def on_error(error_msg):
            logger.warning(f"Failed to disableBsqSwapOffer {open_offer.get_short_id()}")

        self.offer_book_service.remove_offer(
            open_offer.get_offer().offer_payload_base, on_success, on_error
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Handlers
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _on_open_offers_added(self, offers_list: list["OpenOffer"]):
        for open_offer in offers_list:
            if (
                open_offer.get_offer().is_bsq_swap_offer
                and not open_offer.is_deactivated
            ):
                if self._is_proof_of_work_invalid(open_offer.get_offer()):
                    UserThread.execute(
                        lambda: self._redo_proof_of_work_and_republish(open_offer)
                    )
                else:
                    open_bsq_swap_offer = OpenBsqSwapOffer(
                        open_offer,
                        self,
                        self.fee_service,
                        self.btc_wallet_service,
                        self.bsq_wallet_service,
                    )
                    offer_id = open_offer.get_id()
                    if offer_id in self.open_bsq_swap_offers_by_id:
                        self.open_bsq_swap_offers_by_id[offer_id].remove_listeners()
                    self.open_bsq_swap_offers_by_id[offer_id] = open_bsq_swap_offer
                    open_bsq_swap_offer.apply_funding_state()

    def _on_open_offers_removed(self, offers_list: list["OpenOffer"]):
        for open_offer in offers_list:
            if open_offer.get_offer().is_bsq_swap_offer:
                offer_id = open_offer.get_id()
                if offer_id in self.open_bsq_swap_offers_by_id:
                    self.open_bsq_swap_offers_by_id[offer_id].remove_listeners()
                    del self.open_bsq_swap_offers_by_id[offer_id]

    def _on_proof_of_work_difficulty_changed(self):
        for open_bsq_swap_offer in self.open_bsq_swap_offers_by_id.values():
            if (
                not open_bsq_swap_offer.open_offer.is_deactivated
                and not open_bsq_swap_offer.open_offer.bsq_swap_offer_has_missing_funds
                and self._is_proof_of_work_invalid(open_bsq_swap_offer.open_offer.offer)
            ):
                UserThread.execute(
                    lambda: self._redo_proof_of_work_and_republish(
                        open_bsq_swap_offer.open_offer
                    )
                )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Proof of work
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _redo_proof_of_work_and_republish(self, open_offer: "OpenOffer"):
        # This triggers our _on_open_offers_removed handler so we don't handle removal here
        self.open_offer_manager.remove_open_offer(open_offer)

        new_offer_id = OfferUtil.get_offer_id_with_mutation_counter(open_offer.get_id())
        node_address = open_offer.get_offer().maker_node_address
        assert node_address is not None, "Maker node address must not be None"

        difficulty = self._get_pow_difficulty()

        def on_pow_complete(f: Future["ProofOfWork"]):
            try:
                proof_of_work = f.result()

                def execute_on_user_thread():
                    # We mutate the offerId with a postfix counting the mutations to get a new unique id.
                    # This helps to avoid issues with getting added/removed at some delayed moment the offer
                    new_payload = BsqSwapOfferPayload.from_other(
                        open_offer.get_bsq_swap_offer_payload(),
                        new_offer_id,
                        proof_of_work,
                    )
                    new_offer = Offer(new_payload)
                    new_offer.state = OfferState.AVAILABLE

                    check_argument(
                        not open_offer.is_deactivated,
                        "We must not get called at _redo_proof_of_work_and_republish if offer was deactivated"
                    )

                    new_open_offer = OpenOffer(new_offer)
                    if not new_open_offer.is_deactivated:
                        self.open_offer_manager.maybe_republish_offer(new_open_offer)

                    # This triggers our _on_open_offers_added handler so we don't handle adding to our list here
                    self.open_offer_manager.add_open_bsq_swap_offer(new_open_offer)

                UserThread.execute(execute_on_user_thread)
            except Exception as e:
                logger.error(str(e))

        self._get_pow_service().mint_with_ids(
            new_offer_id,
            node_address.get_full_address(),
            difficulty,
        ).add_done_callback(on_pow_complete)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Utils
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _is_proof_of_work_invalid(self, offer: "Offer") -> bool:
        return not self.filter_manager.is_proof_of_work_valid(offer)

    def _get_pow_difficulty(self) -> float:
        return (
            self.filter_manager.get_filter().pow_difficulty
            if self.filter_manager.get_filter() is not None
            else 0.0
        )

    def _get_pow_service(self) -> "ProofOfWorkService":
        enabled_versions = self.filter_manager.get_enabled_pow_versions()
        service = next(
            (
                pow_service_for_version(v)
                for v in enabled_versions
                if pow_service_for_version(v) is not None
            ),
            None,
        )
        if service is None:
            # We cannot exit normally, else we get caught in an infinite loop generating invalid PoWs
            raise RuntimeError("Could not find a suitable PoW version to use")
        logger.info(
            f"Selected PoW version {service.version}, service instance {service}"
        )
        return service
