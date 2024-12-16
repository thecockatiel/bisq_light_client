from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Set, Collection, List, Optional

from bisq.common.handlers.error_message_handler import ErrorMessageHandler
from bisq.common.handlers.result_handler import ResultHandler
from bisq.core.locale.res import Res
from bisq.core.network.p2p.bootstrap_listener import BootstrapListener
from bisq.core.network.p2p.storage.hash_map_changed_listener import (
    HashMapChangedListener,
)
from bisq.core.offer.offer_book_changed_listener import OfferBookChangedListener
from bisq.core.offer.offer_for_json import OfferForJson
from bisq.core.offer.offer_payload_base import OfferPayloadBase
from bisq.core.offer.offer import Offer
from bisq.common.user_thread import UserThread
from bisq.core.util.json_util import JsonUtil

if TYPE_CHECKING:
    from bisq.core.network.p2p.storage.payload.protected_storage_entry import (
        ProtectedStorageEntry,
    )
    from bisq.common.file.json_file_manager import JsonFileManager
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.provider.price.price_feed_service import PriceFeedService


class OfferBookService:
    """
    Handles storage and retrieval of offers.
    Uses an invalidation flag to only request the full offer map in case there was a change.
    """

    def __init__(
        self,
        p2p_service: "P2PService",
        price_feed_service: "PriceFeedService",
        filter_manager: "FilterManager",
        storage_dir: Path,
        dump_statistics: bool,
    ):
        self.p2p_service = p2p_service
        self.price_feed_service = price_feed_service
        self.filter_manager = filter_manager
        self.offer_book_changed_listeners: set[OfferBookChangedListener] = set()
        self.json_file_manager = JsonFileManager(storage_dir)

        class HashMapListener(HashMapChangedListener):
            def on_added(self_, entries: Collection["ProtectedStorageEntry"]):
                for entry in entries:
                    if isinstance(entry.protected_storage_payload, OfferPayloadBase):
                        payload = entry.protected_storage_payload
                        offer = Offer(payload)
                        offer.price_feed_service = self.price_feed_service
                        for listener in self.offer_book_changed_listeners:
                            listener.on_added(offer)

            def on_removed(self_, entries: Collection["ProtectedStorageEntry"]):
                for entry in entries:
                    if isinstance(entry.protected_storage_payload, OfferPayloadBase):
                        payload = entry.protected_storage_payload
                        offer = Offer(payload)
                        offer.price_feed_service = self.price_feed_service
                        for listener in self.offer_book_changed_listeners:
                            listener.on_removed(offer)

        p2p_service.add_hash_set_changed_listener(HashMapListener())

        if dump_statistics:

            class StatisticsListener(BootstrapListener):
                def on_data_received(self_):
                    class StatsOfferListener(OfferBookChangedListener):
                        def on_added(self__, offer):
                            self._do_dump_statistics()

                        def on_removed(self__, offer):
                            self._do_dump_statistics()

                    self.add_offer_book_changed_listener(StatsOfferListener())
                    UserThread.run_after(self._do_dump_statistics, timedelta(seconds=1))

            p2p_service.add_p2p_service_listener(StatisticsListener())

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_offer(
        self,
        offer: "Offer",
        result_handler: ResultHandler,
        error_message_handler: ErrorMessageHandler,
    ) -> None:
        if self.filter_manager.require_update_to_new_version_for_trading():
            error_message_handler(Res.get("popup.warning.mandatoryUpdate.trading"))
            return

        result = self.p2p_service.add_protected_storage_entry(offer.offer_payload_base)
        if result:
            result_handler()
        else:
            error_message_handler("Add offer failed")

    def refresh_ttl(
        self,
        offer_payload_base: "OfferPayloadBase",
        result_handler: ResultHandler,
        error_message_handler: ErrorMessageHandler,
    ) -> None:
        if self.filter_manager.require_update_to_new_version_for_trading():
            error_message_handler(Res.get("popup.warning.mandatoryUpdate.trading"))
            return

        result = self.p2p_service.refresh_ttl(offer_payload_base)
        if result:
            result_handler()
        else:
            error_message_handler("Refresh TTL failed.")

    def activate_offer(
        self,
        offer: "Offer",
        result_handler: Optional[ResultHandler] = None,
        error_message_handler: Optional[ErrorMessageHandler] = None,
    ) -> None:
        self.add_offer(offer, result_handler, error_message_handler)

    def deactivate_offer(
        self,
        offer_payload_base: "OfferPayloadBase",
        result_handler: Optional[ResultHandler] = None,
        error_message_handler: Optional[ErrorMessageHandler] = None,
    ) -> None:
        self.remove_offer(offer_payload_base, result_handler, error_message_handler)

    def remove_offer(
        self,
        offer_payload_base: "OfferPayloadBase",
        result_handler: Optional[ResultHandler] = None,
        error_message_handler: Optional[ErrorMessageHandler] = None,
    ) -> None:
        if self.p2p_service.remove_data(offer_payload_base):
            if result_handler:
                result_handler()
        else:
            if error_message_handler:
                error_message_handler("Remove offer failed")

    def get_offers(self) -> List[Offer]:
        offers = []
        for data in self.p2p_service.get_data_map().values():
            if isinstance(data.protected_storage_payload, OfferPayloadBase):
                offer = Offer(data.protected_storage_payload)
                offer.price_feed_service = self.price_feed_service
                offers.append(offer)
        return offers

    def remove_offer_at_shut_down(self, offer_payload_base: "OfferPayloadBase") -> None:
        self.remove_offer(offer_payload_base, None, None)

    @property
    def is_bootstrapped(self) -> bool:
        return self.p2p_service.is_bootstrapped

    def add_offer_book_changed_listener(
        self, offer_book_changed_listener: OfferBookChangedListener
    ) -> None:
        self.offer_book_changed_listeners.add(offer_book_changed_listener)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _do_dump_statistics(self) -> None:
        offers = [
            offer
            for offer in self.get_offers()
            if not offer.is_use_market_based_price()
            or self.price_feed_service.get_market_price(offer.get_currency_code())
            is not None
        ]

        offer_json_list = []
        for offer in offers:
            try:
                offer_json = OfferForJson(
                    direction=offer.direction,
                    currency_code=offer.currency_code,
                    min_amount=offer.min_amount,
                    amount=offer.amount,
                    price=offer.get_price(),
                    date=offer.date,
                    id=offer.id,
                    use_market_based_price=offer.is_use_market_based_price,
                    market_price_margin=offer.market_price_margin,
                    payment_method=offer.payment_method,
                )
                offer_json_list.append(offer_json)
            except Exception:
                # Skip corrupted offers
                continue

        self.json_file_manager.write_to_disc_threaded(
            JsonUtil.object_to_json(offer_json_list), "offers_statistics"
        )
