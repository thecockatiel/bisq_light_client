from collections import defaultdict
from datetime import timedelta
import logging
from typing import TYPE_CHECKING, Optional, TypeVar, cast
from collections.abc import Callable
from bisq.common.crypto.hash import get_32_byte_hash
from bisq.common.crypto.key_pair import KeyPair
from bisq.common.crypto.sig import Sig, DSA
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.protocol.network.get_data_response_priority import (
    GetDataResponsePriority,
)
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.network.connection import Connection
from bisq.core.network.p2p.network.connection_listener import ConnectionListener
from bisq.core.network.p2p.network.message_listener import MessageListener
from bisq.core.network.p2p.peers.broadcast_handler import BroadcastHandler
from bisq.core.network.p2p.peers.getdata.messages.get_data_response import (
    GetDataResponse,
)
from bisq.core.network.p2p.peers.getdata.messages.get_updated_data_request import (
    GetUpdatedDataRequest,
)
from bisq.core.network.p2p.peers.getdata.messages.preliminary_get_data_request import (
    PreliminaryGetDataRequest,
)
from bisq.core.network.p2p.persistence.historical_data_store_service import (
    HistoricalDataStoreService,
)
from bisq.core.network.p2p.persistence.protected_data_store_service import (
    ProtectedDataStoreService,
)
from bisq.core.network.p2p.storage.data_and_seq_nr_pair import DataAndSeqNrPair
from bisq.core.network.p2p.storage.messages.add_data_message import AddDataMessage
from bisq.core.network.p2p.storage.messages.add_once_payload import AddOncePayload
from bisq.core.network.p2p.storage.messages.add_persistable_network_payload_message import (
    AddPersistableNetworkPayloadMessage,
)
from bisq.core.network.p2p.storage.messages.broadcast_message import BroadcastMessage
from bisq.core.network.p2p.storage.messages.refresh_offer_message import (
    RefreshOfferMessage,
)
from bisq.core.network.p2p.storage.messages.remove_data_message import RemoveDataMessage
from bisq.core.network.p2p.storage.messages.remove_mailbox_data_message import (
    RemoveMailboxDataMessage,
)
from bisq.core.network.p2p.storage.payload.capability_requiring_payload import (
    CapabilityRequiringPayload,
)
from bisq.core.network.p2p.storage.payload.data_sorted_truncatable_payload import (
    DateSortedTruncatablePayload,
)
from bisq.core.network.p2p.storage.payload.data_tolerant_payload import (
    DateTolerantPayload,
)
from bisq.core.network.p2p.storage.payload.mailbox_storage_payload import (
    MailboxStoragePayload,
)
from bisq.core.network.p2p.storage.payload.persistable_network_payload import (
    PersistableNetworkPayload,
)
from bisq.core.network.p2p.storage.payload.process_once_persistable_network_payload import (
    ProcessOncePersistableNetworkPayload,
)
from bisq.core.network.p2p.storage.payload.protected_storage_entry import (
    ProtectedStorageEntry,
)
from bisq.core.network.p2p.storage.payload.protected_storage_payload import (
    ProtectedStoragePayload,
)
from bisq.core.network.p2p.storage.payload.requires_owner_is_online_payload import (
    RequiresOwnerIsOnlinePayload,
)
from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray
from bisq.core.network.p2p.storage.storage_map_value import StorageMapValue
from bisq.common.setup.log_setup import get_logger
from utils.concurrency import AtomicBoolean, AtomicInt, ThreadSafeDict, ThreadSafeSet
from utils.data import SimpleProperty, combine_simple_properties
from utils.formatting import to_truncated_string
from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.core.network.p2p.storage.sequence_number_map import SequenceNumberMap
from bisq.core.network.p2p.storage.payload.protected_mailbox_storage_entry import (
    ProtectedMailboxStorageEntry,
)

if TYPE_CHECKING:
    from utils.clock import Clock
    from bisq.common.timer import Timer
    from bisq.core.network.p2p.persistence.append_only_data_store_listener import (
        AppendOnlyDataStoreListener,
    )
    from bisq.core.network.p2p.storage.hash_map_changed_listener import (
        HashMapChangedListener,
    )
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.p2p.persistence.append_only_data_store_service import (
        AppendOnlyDataStoreService,
    )
    from bisq.core.network.p2p.persistence.resource_data_store_service import (
        ResourceDataStoreService,
    )
    from bisq.core.network.p2p.persistence.removed_payloads_service import (
        RemovedPayloadsService,
    )
    from bisq.core.network.p2p.peers.broadcaster import Broadcaster
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.network.p2p.peers.getdata.messages.get_data_request import (
        GetDataRequest,
    )
    from bisq.common.capabilities import Capabilities
    from bisq.core.network.p2p.network.close_connection_reason import (
        CloseConnectionReason,
    )
    from bisq.common.persistence.persistence_manager import PersistenceManager


logger = get_logger(__name__)

T = TypeVar("T", bound=NetworkPayload)


class P2PDataStorage(MessageListener, ConnectionListener, PersistedDataHost):
    # How many days to keep an entry before it is purged.
    PURGE_AGE_DAYS = 10
    CHECK_TTL_INTERVAL_SEC = 60

    def __init__(
        self,
        network_node: "NetworkNode",
        broadcaster: "Broadcaster",
        append_only_data_store_service: "AppendOnlyDataStoreService",
        protected_data_store_service: "ProtectedDataStoreService",
        resource_data_store_service: "ResourceDataStoreService",
        persistence_manager: "PersistenceManager[SequenceNumberMap]",
        removed_payloads_service: "RemovedPayloadsService",
        clock: "Clock",
        max_sequence_number_map_size_before_purge: int,
    ):
        self.initial_request_applied = False

        self.broadcaster = broadcaster
        self.append_only_data_store_service = append_only_data_store_service
        self.protected_data_store_service = protected_data_store_service
        self.resource_data_store_service = resource_data_store_service

        self.map: ThreadSafeDict["StorageByteArray", "ProtectedStorageEntry"] = (
            ThreadSafeDict()
        )
        self.hash_map_changed_listeners: ThreadSafeSet["HashMapChangedListener"] = (
            ThreadSafeSet()
        )
        self.remove_expired_entries_timer: Timer = None

        self.persistence_manager = persistence_manager

        self.sequence_number_map: "SequenceNumberMap" = SequenceNumberMap()
        self.append_only_data_store_listeners: ThreadSafeSet[
            "AppendOnlyDataStoreListener"
        ] = ThreadSafeSet()
        self.removed_payloads_service = removed_payloads_service
        self.clock = clock

        # The maximum number of items that must exist in the SequenceNumberMap before it is scheduled for a purge
        # which removes entries after PURGE_AGE_DAYS.
        self.max_sequence_number_map_size_before_purge = (
            max_sequence_number_map_size_before_purge
        )

        self.read_from_resources_complete_property = SimpleProperty(False)

        self.filter_predicate: Optional[Callable[[ProtectedStoragePayload], bool]] = (
            None  # Set from FilterManager
        )

        network_node.add_message_listener(self)
        network_node.add_connection_listener(self)

        self.persistence_manager.initialize(
            self.sequence_number_map, PersistenceManagerSource.PRIVATE_LOW_PRIO
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PersistedDataHost
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def read_persisted(self, complete_handler: Callable[[], None]):
        def callback(persisted: "SequenceNumberMap"):
            self.sequence_number_map.map = self.get_purged_sequence_number_map(
                persisted.map
            )
            complete_handler()

        self.persistence_manager.read_persisted(callback, complete_handler)

    def read_persisted_sync(self):
        """Uses synchronous execution on the userThread. Only used by tests. The async methods should be used by app code."""
        persisted = self.persistence_manager.get_persisted()
        if persisted:
            self.sequence_number_map.map = self.get_purged_sequence_number_map(
                persisted.map
            )

    # Threading is done on the persistenceManager level
    def read_from_resources(self, postfix: str, complete_handler: Callable[[], None]):
        append_only_data_store_service_ready = SimpleProperty(False)
        protected_data_store_service_ready = SimpleProperty(False)
        resource_data_store_service_ready = SimpleProperty(False)

        self.read_from_resources_complete_property = combine_simple_properties(
            append_only_data_store_service_ready,
            protected_data_store_service_ready,
            resource_data_store_service_ready,
            transform=all,
        )

        self.read_from_resources_complete_property.add_listener(
            lambda e: complete_handler() if e.new_value else None
        )

        self.append_only_data_store_service.read_from_resources(
            postfix, lambda: append_only_data_store_service_ready.set(True)
        )
        self.protected_data_store_service.read_from_resources(
            postfix,
            lambda: (
                self.map.update(self.protected_data_store_service.get_map()),
                protected_data_store_service_ready.set(True),
            ),
        )
        self.resource_data_store_service.read_from_resources(
            postfix, lambda: resource_data_store_service_ready.set(True)
        )

    # Uses synchronous execution on the userThread. Only used by tests. The async methods should be used by app code.
    def read_from_resources_sync(self, postfix: str):
        self.append_only_data_store_service.read_from_resources_sync(postfix)
        self.protected_data_store_service.read_from_resources_sync(postfix)
        self.resource_data_store_service.read_from_resources_sync(postfix)

        self.map.update(self.protected_data_store_service.get_map())

    # We get added mailbox message data from MailboxMessageService. We want to add those early so we can get it added
    # to our excluded keys to reduce initial data response data size.
    def add_protected_mailbox_storage_entry_to_map(
        self, protected_storage_entry: "ProtectedStorageEntry"
    ):
        protected_storage_payload = protected_storage_entry.protected_storage_payload
        hash_of_payload = StorageByteArray(get_32_byte_hash(protected_storage_payload))
        self.map[hash_of_payload] = protected_storage_entry

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // RequestData API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def build_preliminary_get_data_request(self, nonce: int):
        """Returns a PreliminaryGetDataRequest that can be sent to a peer node to request missing Payload data."""
        return PreliminaryGetDataRequest(
            nonce=nonce, excluded_keys=self.get_known_payload_hashes()
        )

    def build_get_updated_data_request(
        self, sender_node_address: "NodeAddress", nonce: int
    ):
        """Returns a GetUpdatedDataRequest that can be sent to a peer node to request missing Payload data."""
        return GetUpdatedDataRequest(
            sender_node_address=sender_node_address,
            nonce=nonce,
            excluded_keys=self.get_known_payload_hashes(),
        )

    def get_known_payload_hashes(self) -> set[bytes]:
        """Returns the set of known payload hashes. This is used in the GetData path to request missing data from peer nodes"""
        # We collect the keys of the PersistableNetworkPayload items so we exclude them in our request.
        # PersistedStoragePayload items don't get removed, so we don't have an issue with the case that
        # an object gets removed in between PreliminaryGetDataRequest and the GetUpdatedDataRequest and we would
        # miss that event if we do not load the full set or use some delta handling.
        map_for_data_request = self.get_map_for_data_request()
        excluded_keys = self.get_keys_as_byte_set(map_for_data_request)
        excluded_keys_from_protected_storage_entry_map = self.get_keys_as_byte_set(
            self.map
        )
        excluded_keys.update(excluded_keys_from_protected_storage_entry_map)
        return excluded_keys

    def build_get_data_response(
        self,
        get_data_request: "GetDataRequest",
        max_entries_per_type: int,
        was_persistable_network_payloads_truncated: "AtomicBoolean",
        was_protected_storage_entries_truncated: "AtomicBoolean",
        peer_capabilities: "Capabilities",
    ):
        """Returns a GetDataResponse object that contains the Payloads known locally, but not remotely."""
        excluded_keys_as_byte_array = (
            StorageByteArray.convert_bytes_set_to_bytearray_set(
                get_data_request.excluded_keys
            )
        )

        # Pre v 1.4.0 requests do not have set the requesters version field so it is null.
        # The methods in HistoricalDataStoreService will return all historical data in that case.
        # mapForDataResponse contains the filtered by version data from HistoricalDataStoreService as well as all other
        # maps of the remaining appendOnlyDataStoreServices.
        map_for_data_response = self.get_map_for_data_response(get_data_request.version)

        # Give a bit of tolerance for message overhead
        max_size = Connection.MAX_PERMITTED_MESSAGE_SIZE * 0.6

        # 25% of space is allocated for PersistableNetworkPayloads
        limit = round(max_size * 0.25)

        filtered_persistable_network_payloads = self.filter_known_hashes(
            to_filter=map_for_data_response,
            as_payload=lambda x: x,
            known_hashes=excluded_keys_as_byte_array,
            peer_capabilities=peer_capabilities,
            max_entries=max_entries_per_type,
            limit=limit,
            out_truncated=was_persistable_network_payloads_truncated,
            is_persistable_network_payload=True,
        )
        logger.info(
            f"{len(filtered_persistable_network_payloads)} PersistableNetworkPayload entries remained after filtered by excluded keys. "
            + f"Original map had {len(map_for_data_response)} entries."
        )
        logger.trace(
            f"## buildGetDataResponse filteredPersistableNetworkPayloadHashes={[payload.get_hash().hex() for payload in filtered_persistable_network_payloads]}"
        )

        # We give 75% space to ProtectedStorageEntries as they contain MailBoxMessages and those can be larger.
        limit = round(max_size * 0.75)
        _as_payload: Callable[["ProtectedStorageEntry"], "NetworkPayload"] = (
            lambda x: x.protected_storage_payload
        )
        filtered_protected_storage_entries = self.filter_known_hashes(
            to_filter=self.map,
            as_payload=_as_payload,
            known_hashes=excluded_keys_as_byte_array,
            peer_capabilities=peer_capabilities,
            max_entries=max_entries_per_type,
            limit=limit,
            out_truncated=was_protected_storage_entries_truncated,
            is_persistable_network_payload=False,
        )
        logger.info(
            f"{len(filtered_protected_storage_entries)} ProtectedStorageEntry entries remained after filtered by excluded keys. "
            f"Original map had {len(self.map)} entries."
        )
        logger.trace(
            f"## buildGetDataResponse filteredProtectedStorageEntryHashes={[StorageByteArray(get_32_byte_hash(entry.protected_storage_payload)) for entry in filtered_protected_storage_entries]}"
        )

        was_truncated = (
            was_persistable_network_payloads_truncated.get()
            or was_protected_storage_entries_truncated.get()
        )
        return GetDataResponse(
            data_set=filtered_protected_storage_entries,
            persistable_network_payload_set=filtered_persistable_network_payloads,
            request_nonce=get_data_request.nonce,
            is_get_updated_data_response=isinstance(
                get_data_request, GetUpdatedDataRequest
            ),  # NOTE: ???
            was_truncated=was_truncated,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Utils for collecting the exclude hashes
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_map_for_data_request(
        self,
    ) -> dict["StorageByteArray", "PersistableNetworkPayload"]:
        """Returns a map of payload data excluding historical data for data requests"""
        result = {}
        for service in self.append_only_data_store_service.services:
            if isinstance(service, HistoricalDataStoreService):
                # As we add the version to our request we only use the live data.
                # Eventually missing data will be derived from the version.
                service_map = service.get_map_of_live_data()
            else:
                service_map = service.get_map()

            result.update(service_map)
            logger.debug(
                f"We added {len(service_map)} entries from {service.__class__.__name__} to the excluded key set of our request"
            )

        return result

    def get_map_for_data_response(
        self, requesters_version: str
    ) -> dict["StorageByteArray", "PersistableNetworkPayload"]:
        """Returns a map of payload data including historical data since the requester's version"""
        result = {}
        for service in self.append_only_data_store_service.services:
            if isinstance(service, HistoricalDataStoreService):
                service_map = service.get_map_since_version(requesters_version)
            else:
                service_map = service.get_map()

            result.update(service_map)
            logger.info(
                f"We added {len(service_map)} entries from {service.__class__.__name__} to be filtered by excluded keys"
            )

        return result

    @staticmethod
    def filter_known_hashes(
        to_filter: dict[StorageByteArray, T],
        as_payload: Callable[[T], "NetworkPayload"],
        known_hashes: set[StorageByteArray],
        peer_capabilities: "Capabilities",
        max_entries: int,
        limit: int,
        out_truncated: "AtomicBoolean",
        is_persistable_network_payload: bool,
    ) -> set[T]:
        """Generic function that filters a dict[StorageByteArray, (ProtectedStorageEntry || PersistableNetworkPayload)]
        by a given set of keys and peer capabilities."""

        logger.info(
            f"Filter {'PersistableNetworkPayload' if is_persistable_network_payload else 'ProtectedStorageEntry'} "
            f"data based on {len(known_hashes)} knownHashes"
        )

        total_size = AtomicInt()
        exceeded_size_limit = AtomicBoolean()

        # Count items by class name
        num_items_by_class_name = defaultdict(AtomicInt)
        for entry in to_filter.values():
            name = as_payload(entry).__class__.__name__
            num_items_by_class_name[name].increment_and_get()
        logger.info(f"numItemsByClassName: {num_items_by_class_name}")

        # Filter items not in known_hashes and should transmit to peer
        filtered_items = [
            item
            for key, item in to_filter.items()
            if key not in known_hashes
            and P2PDataStorage.should_transmit_payload_to_peer(
                peer_capabilities, as_payload(item)
            )
        ]

        result_items = []

        # Truncation follows this rules
        # 1. Add all payloads with GetDataResponsePriority.MID
        # 2. Add all payloads with GetDataResponsePriority.LOW && !DateSortedTruncatablePayload until exceededSizeLimit is reached
        # 3. if(!exceededSizeLimit) Add all payloads with GetDataResponsePriority.LOW && DateSortedTruncatablePayload until
        #    exceededSizeLimit is reached and truncate by maxItems (sorted by date). We add the sublist to our resultItems in
        #    reverse order so in case we cut off at next step we cut off oldest items.
        # 4. We truncate list if resultList size > maxEntries
        # 5. Add all payloads with GetDataResponsePriority.HIGH

        # 1. Add all payloads with GetDataResponsePriority.MID
        mid_prio_items = [
            item
            for item in filtered_items
            if item.get_data_response_priority() == GetDataResponsePriority.MID
        ]
        result_items.extend(mid_prio_items)
        logger.info(
            f"Number of items with GetDataResponsePriority.MID: {len(mid_prio_items)}"
        )

        # 2. Add LOW priority non-DateSortedTruncatable items until exceededSizeLimit is reached
        def check_size_limit(item: "NetworkPayload"):
            if exceeded_size_limit.get():
                return False
            if total_size.add_and_get(item.to_proto_message().ByteSize()) > limit:
                exceeded_size_limit.set(True)
                return False
            return True

        low_prio_items = [
            item
            for item in filtered_items
            if item.get_data_response_priority() == GetDataResponsePriority.LOW
            and not isinstance(as_payload(item), DateSortedTruncatablePayload)
            and check_size_limit(item)
        ]
        result_items.extend(low_prio_items)
        logger.info(
            f"Number of items with GetDataResponsePriority.LOW and !DateSortedTruncatablePayload: {len(low_prio_items)}. Exceeded size limit: {exceeded_size_limit.get()}"
        )

        # 3. if(!exceededSizeLimit) Add all payloads with GetDataResponsePriority.LOW && DateSortedTruncatablePayload until
        #    exceededSizeLimit is reached and truncate by maxItems (sorted by date). We add the sublist to our resultItems in
        #    reverse order so in case we cut off at next step we cut off oldest items.
        if not exceeded_size_limit.get():
            date_sorted_items = [
                item
                for item in filtered_items
                if item.get_data_response_priority() == GetDataResponsePriority.LOW
                and isinstance(as_payload(item), DateSortedTruncatablePayload)
                and check_size_limit(item)
            ]

            if date_sorted_items:
                date_sorted_items.sort(
                    key=lambda x: cast(  # We checked earlier that It's for sure DateSortedTruncatablePayload
                        DateSortedTruncatablePayload, as_payload(x)
                    ).get_date()
                )
                max_items = cast(
                    DateSortedTruncatablePayload, as_payload(date_sorted_items[0])
                ).max_items()
                size = len(date_sorted_items)
                if size > max_items:
                    from_index = size - max_items
                    date_sorted_items = date_sorted_items[from_index:size]
                    out_truncated.set(True)
                    logger.info(f"Num truncated dateSortedItems {size}")
                    logger.info(
                        f"Removed oldest {from_index} dateSortedItems as we exceeded {max_items}"
                    )

            logger.info(
                f"Number of items with GetDataResponsePriority.LOW and DateSortedTruncatablePayload: {len(date_sorted_items)}. Was truncated: {out_truncated.get()}"
            )

            # We reverse sorting so in case we get truncated we cut off the older items
            date_sorted_items.sort(
                key=lambda x: cast(
                    DateSortedTruncatablePayload, as_payload(x)
                ).get_date(),
                reverse=True,
            )
            result_items.extend(date_sorted_items)
        else:
            logger.info(
                f"No dateSortedItems added as we exceeded already the exceededSizeLimit of {limit}"
            )

        # 4. We truncate list if resultList size > maxEntries
        size = len(result_items)
        if size > max_entries:
            result_items = result_items[:max_entries]
            out_truncated.set(True)
            logger.info(
                f"Removed last {size - max_entries} items as we exceeded {max_entries}"
            )

        out_truncated.set(out_truncated.get() or exceeded_size_limit.get())

        # 5. Add all payloads with GetDataResponsePriority.HIGH
        high_prio_items = [
            item
            for item in filtered_items
            if item.get_data_response_priority() == GetDataResponsePriority.HIGH
        ]
        result_items.extend(high_prio_items)
        logger.info(
            f"Number of items with GetDataResponsePriority.HIGH: {len(high_prio_items)}"
        )
        logger.info(f"Number of result items we send to requester: {len(result_items)}")
        return set(result_items)

    def get_persistable_network_payload_collection(
        self,
    ) -> list["PersistableNetworkPayload"]:
        return list(self.get_map_for_data_request().values())

    def get_keys_as_byte_set(
        self, map_obj: dict["StorageByteArray", "PersistablePayload"]
    ) -> set[bytes]:
        return {key.bytes for key in map_obj.keys()}

    # NOTE: For altering peer behavior later?
    @staticmethod
    def should_transmit_payload_to_peer(
        peer_capabilities: "Capabilities", payload: "NetworkPayload"
    ) -> bool:
        """Returns true if a Payload should be transmitted to a peer given the peer's supported capabilities."""
        # Sanity check to ensure this isn't used outside P2PDataStorage
        if not isinstance(
            payload, (ProtectedStoragePayload, PersistableNetworkPayload)
        ):
            return False

        # If the payload doesn't have a required capability, we should transmit it
        if not isinstance(payload, CapabilityRequiringPayload):
            return True

        # Otherwise, only transmit the Payload if the peer supports all capabilities required by the payload
        should_transmit = peer_capabilities.contains_all(
            payload.get_required_capabilities()
        )

        if not should_transmit:
            logger.debug(
                "We do not send the message to the peer because they do not support the required capability for that message type.\n"
                f"storagePayload is: {to_truncated_string(payload)}"
            )

        return should_transmit

    def process_get_data_response(
        self, get_data_response: "GetDataResponse", sender: "NodeAddress"
    ):
        """
        Processes a GetDataResponse message and updates internal state. Does not broadcast updates to the P2P network
        or domain listeners.
        """
        protected_storage_entries = get_data_response.data_set
        persistable_network_payload_set = (
            get_data_response.persistable_network_payload_set
        )

        ts = self.clock.millis()
        for protected_storage_entry in protected_storage_entries:
            # We rebroadcast high priority data after a delay for better resilience
            if (
                protected_storage_entry.protected_storage_payload.get_data_response_priority()
                == GetDataResponsePriority.HIGH
            ):
                # We rebroadcast high priority data after a delay for better resilience
                def rebroadcast():
                    logger.info(
                        f"Rebroadcast {protected_storage_entry.protected_storage_payload.__class__.__name__}"
                    )
                    self.broadcaster.broadcast(
                        AddDataMessage(protected_storage_entry=protected_storage_entry),
                        sender,
                        None,
                    )

                UserThread.run_after(rebroadcast, timedelta(seconds=60))

            # We don't broadcast here (last param) as we are only connected to the seed node and would be pointless
            self.add_protected_storage_entry(
                protected_storage_entry, sender, None, False
            )

        logger.info(
            f"Processing {len(protected_storage_entries)} protectedStorageEntries took {self.clock.millis() - ts} ms."
        )

        ts = self.clock.millis()
        for payload in persistable_network_payload_set:
            if isinstance(payload, ProcessOncePersistableNetworkPayload):
                # We use an optimized method as many checks are not required in that case to avoid
                # performance issues.
                # Processing 82645 items took now 61 ms compared to earlier version where it took ages (> 2min). # NOTE: TODO: unchecked performance in python version
                # Usually we only get about a few hundred or max. a few 1000 items. 82645 is all
                # trade stats and all account age witness data.

                # We only apply it once from first response
                if not self.initial_request_applied or get_data_response.was_truncated:
                    self.add_persistable_network_payload_from_initial_request(payload)
            else:
                # We don't broadcast here as we are only connected to the seed node and would be pointless
                self._add_persistable_network_payload_internal(
                    payload, sender, False, False, False
                )

        logger.info(
            f"Processing {len(persistable_network_payload_set)} persistableNetworkPayloads took {self.clock.millis() - ts} ms."
        )

        # We only process PersistableNetworkPayloads implementing ProcessOncePersistableNetworkPayload once. It can cause performance
        # issues and since the data is rarely out of sync it is not worth it to apply them from multiple peers during
        # startup.
        self.initial_request_applied = True

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def shut_down(self):
        if self.remove_expired_entries_timer:
            self.remove_expired_entries_timer.stop()

    def remove_expired_entries(self):
        # The moment when an object becomes expired will not be synchronous in the network and we could
        # get add messages after the object has expired. To avoid repeated additions of already expired
        # object when we get it sent from new peers, we don't remove the sequence number from the map.
        # That way an ADD message for an already expired data will fail because the sequence number
        # is equal and not larger as expected.
        to_remove_list = [
            entry for entry in self.map.items() if entry[1].is_expired(self.clock)
        ]

        # Batch processing can cause performance issues, so do all of the removes first, then update the listeners
        # to let them know about the removes.
        if logger.isEnabledFor(logging.DEBUG):
            for item in to_remove_list:
                logger.debug(
                    f"We found an expired data entry. We remove the protectedData:\n\t{to_truncated_string(item[1])}"
                )

        # Remove expired entries
        self.remove_from_map_and_data_store(to_remove_list)

        # Check if we need to purge sequence number map
        if (
            len(self.sequence_number_map)
            > self.max_sequence_number_map_size_before_purge
        ):
            self.sequence_number_map.map = self.get_purged_sequence_number_map(
                self.sequence_number_map.map
            )
            self.request_persistence()

    def on_bootstrapped(self):
        self.remove_expired_entries_timer = UserThread.run_periodically(
            self.remove_expired_entries,
            timedelta(seconds=P2PDataStorage.CHECK_TTL_INTERVAL_SEC),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // MessageListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_message(self, network_envelope: "NetworkEnvelope", connection: "Connection"):
        """Handle incoming network messages"""
        if isinstance(network_envelope, BroadcastMessage):
            peers_node_address = connection.peers_node_address
            if peers_node_address:
                if isinstance(network_envelope, AddDataMessage):
                    self.add_protected_storage_entry(
                        network_envelope.protected_storage_entry,
                        peers_node_address,
                        None,
                        True,
                    )
                elif isinstance(network_envelope, RemoveDataMessage):
                    self.remove(
                        network_envelope.protected_storage_entry, peers_node_address
                    )
                elif isinstance(network_envelope, RemoveMailboxDataMessage):
                    self.remove(
                        network_envelope.protected_mailbox_storage_entry,
                        peers_node_address,
                    )
                elif isinstance(network_envelope, RefreshOfferMessage):
                    self.refresh_ttl(network_envelope, peers_node_address)
                elif isinstance(network_envelope, AddPersistableNetworkPayloadMessage):
                    self._add_persistable_network_payload_internal(
                        network_envelope.persistable_network_payload,
                        peers_node_address,
                        True,
                        False,
                        True,
                    )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // ConnectionListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_connection(self, connection: "Connection"):
        pass

    def on_disconnect(
        self, close_connection_reason: "CloseConnectionReason", connection: "Connection"
    ):
        if close_connection_reason.is_intended:
            return

        peers_node_address = connection.peers_node_address
        if not peers_node_address:
            return

        # Backdate all the eligible payloads based on the node that disconnected
        for protected_storage_entry in self.map.values():
            payload = protected_storage_entry.protected_storage_payload
            if (
                isinstance(payload, RequiresOwnerIsOnlinePayload)
                and payload.get_owner_node_address() == peers_node_address
            ):
                # We only set the data back by half of the TTL and remove the data only if is has
                # expired after that back dating.
                # We might get connection drops which are not caused by the node going offline, so
                # we give more tolerance with that approach, giving the node the chance to
                # refresh the TTL with a refresh message.
                # We observed those issues during stress tests, but it might have been caused by the
                # test set up (many nodes/connections over 1 router)
                # JAVA TODO investigate what causes the disconnections.
                # Usually the are: SOCKET_TIMEOUT ,TERMINATED (EOFException)
                logger.debug(
                    f"Backdating {protected_storage_entry} due to closeConnectionReason={close_connection_reason}"
                )
                protected_storage_entry.back_date()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Client API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_persistable_network_payload(
        self,
        payload: "PersistableNetworkPayload",
        sender: Optional["NodeAddress"],
        allow_re_broadcast: bool,
    ) -> bool:
        """
        Adds a PersistableNetworkPayload to the local P2P data storage. If it does not already exist locally,
        it will be broadcast to the P2P network.

        Args:
            payload: PersistableNetworkPayload to add to the network
            sender: local NodeAddress, if available
            allow_re_broadcast: if the PersistableNetworkPayload should be rebroadcast even if it already exists locally

        Returns:
            bool: True if the PersistableNetworkPayload passes all validation and exists in the P2PDataStore
                 on completion
        """
        return self._add_persistable_network_payload_internal(
            payload, sender, True, allow_re_broadcast, False
        )

    def _add_persistable_network_payload_internal(
        self,
        payload: "PersistableNetworkPayload",
        sender: Optional["NodeAddress"],
        allow_broadcast: bool,
        re_broadcast: bool,
        check_date: bool,
    ) -> bool:
        logger.debug(f"add_persistable_network_payload payload={payload}")

        # Payload hash size does not match expectation for that type of message
        if not payload.verify_hash_size():
            logger.warning(
                "add_persistable_network_payload failed due to unexpected hash size"
            )
            return False

        hash_as_byte_array = StorageByteArray(payload.get_hash())
        payload_hash_already_in_store = (
            hash_as_byte_array in self.append_only_data_store_service.get_map(payload)
        )

        # Store already knows about this payload. Ignore it unless caller specifically requests a republish
        if payload_hash_already_in_store and not re_broadcast:
            logger.debug(
                "add_persistable_network_payload failed due to duplicate payload"
            )
            return False

        # DateTolerantPayloads are only checked for tolerance from the onMessage handler (check_date == True)
        # If not in tolerance, ignore it
        if check_date and isinstance(payload, DateTolerantPayload):
            if not payload.is_date_in_tolerance(self.clock):
                logger.warning(
                    f"add_persistable_network_payload failed due to payload time outside tolerance.\n"
                    f"Payload={payload}; now={self.clock.millis()}"
                )
                return False

        # Add the payload and publish the state update to the appendOnlyDataStoreListeners
        was_added = False
        if not payload_hash_already_in_store:
            was_added = self.append_only_data_store_service.put(
                hash_as_byte_array, payload
            )
            if was_added:
                for listener in self.append_only_data_store_listeners:
                    listener(payload)

        # Broadcast the payload if requested by caller
        if allow_broadcast and was_added:
            self.broadcaster.broadcast(
                AddPersistableNetworkPayloadMessage(
                    persistable_network_payload=payload
                ),
                sender,
            )

        return True

    # When we receive initial data we skip several checks to improve performance. We requested only missing entries so we
    # do not need to check again if the item is contained in the map, which is a bit slow as the map can be very large.
    # Overwriting an entry would be also no issue. We also skip notifying listeners as we get called before the domain
    # is ready so no listeners are set anyway. We might get called twice from a redundant call later, so listeners
    # might be added then but as we have the data already added calling them would be irrelevant as well.
    def add_persistable_network_payload_from_initial_request(
        self, payload: "PersistableNetworkPayload"
    ):
        hash_bytes = payload.get_hash()
        if payload.verify_hash_size():
            hash_as_byte_array = StorageByteArray(hash_bytes)
            self.append_only_data_store_service.put(hash_as_byte_array, payload)
        else:
            logger.warning("We got a hash exceeding our permitted size")

    def add_protected_storage_entry(
        self,
        protected_storage_entry: "ProtectedStorageEntry",
        sender: Optional["NodeAddress"],
        listener: Optional["BroadcastHandler.Listener"],
        allow_broadcast: bool = True,
    ) -> bool:
        """
        Adds a ProtectedStorageEntry to the local P2P data storage and broadcast if all checks have been successful.

        Args:
            protected_storage_entry: ProtectedStorageEntry to add to the network
            sender: Sender's nodeAddress, if available
            listener: optional listener that can be used to receive events on broadcast
            allow_broadcast: Flag to allow broadcast

        Returns:
            bool: True if the ProtectedStorageEntry was added to the local P2P data storage
        """
        protected_storage_payload = protected_storage_entry.protected_storage_payload
        hash_of_payload = StorageByteArray(get_32_byte_hash(protected_storage_payload))

        # We do that check early as it is a very common case for returning, so we return early
        # If we have seen a more recent operation for this payload and we have a payload locally, ignore it
        stored_entry = self.map.get(hash_of_payload)
        if stored_entry is not None and not self.has_sequence_nr_increased(
            protected_storage_entry.sequence_number, hash_of_payload
        ):
            logger.trace(f"## hasSequenceNrIncreased is false. hash={hash_of_payload}")
            return False

        if self.has_already_removed_add_once_payload(
            protected_storage_payload, hash_of_payload
        ):
            logger.trace(
                "## We have already removed that AddOncePayload by a previous removeDataMessage. "
                f"We ignore that message. ProtectedStoragePayload: {protected_storage_payload}"
            )
            return False

        # To avoid that expired data get stored and broadcast we check for expire date.
        if protected_storage_entry.is_expired(self.clock):
            peer = sender.get_full_address() if sender else "sender is null"
            logger.trace(
                f"## We received an expired protectedStorageEntry from peer {peer}. "
                f"ProtectedStoragePayload={protected_storage_entry.protected_storage_payload.__class__.__name__}"
            )
            return False

        # We want to allow add operations for equal sequence numbers if we don't have the payload locally. This is
        # the case for non-persistent Payloads that need to be reconstructed from peer and seed nodes each startup.
        sequence_number_map_value = self.sequence_number_map.get(hash_of_payload, None)
        if (
            sequence_number_map_value is not None
            and protected_storage_entry.sequence_number
            < sequence_number_map_value.sequence_nr
        ):
            logger.trace(f"## sequenceNr too low hash={hash_of_payload}")
            return False

        # Verify the ProtectedStorageEntry is well formed and valid for the add operation
        if not protected_storage_entry.is_valid_for_add_operation():
            logger.trace(f"## !isValidForAddOperation hash={hash_of_payload}")
            return False

        # If we have already seen an Entry with the same hash, verify the metadata is equal
        if (
            stored_entry is not None
            and not protected_storage_entry.matches_relevant_pub_key(stored_entry)
        ):
            logger.trace(f"## !matchesRelevantPubKey hash={hash_of_payload}")
            return False

        # Test against filterPredicate set from FilterManager
        if self.filter_predicate is not None and not self.filter_predicate(
            protected_storage_entry.protected_storage_payload
        ):
            logger.debug(
                f"filterPredicate test failed. hashOfPayload={hash_of_payload}"
            )
            return False

        # This is an updated entry. Record it and signal listeners.
        self.map[hash_of_payload] = protected_storage_entry
        for l in self.hash_map_changed_listeners:
            l.on_added([protected_storage_entry])

        # Record the updated sequence number and persist it. Higher delay so we can batch more items.
        self.sequence_number_map[hash_of_payload] = StorageMapValue(
            sequence_nr=protected_storage_entry.sequence_number,
            time_stamp=self.clock.millis(),
        )
        self.request_persistence()

        # Optionally, broadcast the add/update depending on the calling environment
        if allow_broadcast:
            self.broadcaster.broadcast(
                AddDataMessage(protected_storage_entry=protected_storage_entry),
                sender,
                listener,
            )
            logger.trace(
                f"## broadcasted ProtectedStorageEntry. hash={hash_of_payload}"
            )

        # Persist ProtectedStorageEntries carrying PersistablePayload payloads
        if isinstance(protected_storage_payload, PersistablePayload):
            self.protected_data_store_service.put(
                hash_of_payload, protected_storage_entry
            )

        return True

    def republish_existing_protected_mailbox_storage_entry(
        self,
        protected_mailbox_storage_entry: "ProtectedMailboxStorageEntry",
        sender: Optional["NodeAddress"],
        listener: Optional["BroadcastHandler.Listener"],
    ):
        """
        We do not do all checks as it is used for republishing existing mailbox messages from seed nodes which
        only got stored if they had been valid when we received them.

        Args:
            protected_mailbox_storage_entry: ProtectedMailboxStorageEntry to add to the network
            sender: Sender's nodeAddress, if available
            listener: optional listener that can be used to receive events on broadcast
        """
        protected_storage_payload = (
            protected_mailbox_storage_entry.protected_storage_payload
        )
        hash_of_payload = StorageByteArray(get_32_byte_hash(protected_storage_payload))

        # logger.trace("## call republishProtectedStorageEntry hash={}, map={}", hash_of_payload, self.print_map())

        if self.has_already_removed_add_once_payload(
            protected_storage_payload, hash_of_payload
        ):
            logger.trace(
                "## We have already removed that AddOncePayload by a previous removeDataMessage. "
                f"We ignore that message. ProtectedStoragePayload: {protected_storage_payload}"
            )
            return

        self.broadcaster.broadcast(
            AddDataMessage(protected_storage_entry=protected_mailbox_storage_entry),
            sender,
            listener,
        )
        logger.trace(f"## broadcasted ProtectedStorageEntry. hash={hash_of_payload}")

    def has_already_removed_add_once_payload(
        self,
        protected_storage_payload: "ProtectedStoragePayload",
        hash_of_payload: "StorageByteArray",
    ) -> bool:
        """
        Check if an AddOncePayload was previously removed

        Args:
            protected_storage_payload: The payload to check
            hash_of_payload: Hash of the payload

        Returns:
            bool: True if the payload is an AddOncePayload and was previously removed
        """
        return isinstance(
            protected_storage_payload, AddOncePayload
        ) and self.removed_payloads_service.was_removed(hash_of_payload)

    def refresh_ttl(
        self,
        refresh_ttl_message: "RefreshOfferMessage",
        sender: Optional["NodeAddress"],
    ) -> bool:
        """
        Updates a local RefreshOffer with TTL changes and broadcasts those changes to the network

        Args:
            refresh_ttl_message: RefreshOfferMessage containing the update
            sender: local NodeAddress, if available

        Returns:
            bool: True if the RefreshOffer was successfully updated and changes broadcast
        """
        try:
            hash_of_payload = StorageByteArray(refresh_ttl_message.hash_of_payload)
            stored_data = self.map.get(hash_of_payload)

            if stored_data is None:
                logger.debug(
                    "We don't have data for that refresh message in our map. That is expected if we missed the data publishing."
                )
                return False

            stored_entry = self.map.get(hash_of_payload)
            updated_entry = ProtectedStorageEntry(
                protected_storage_payload=stored_entry.protected_storage_payload,
                owner_pub_key=stored_entry.owner_pub_key,
                sequence_number=refresh_ttl_message.sequence_number,
                signature=refresh_ttl_message.signature,
                clock=self.clock,
            )

            # If we have seen a more recent operation for this payload, we ignore the current one
            if not self.has_sequence_nr_increased(
                updated_entry.sequence_number, hash_of_payload
            ):
                return False

            # Verify the updated ProtectedStorageEntry is well formed and valid for update
            if not updated_entry.is_valid_for_add_operation():
                return False

            # Update the hash map with the updated entry
            self.map[hash_of_payload] = updated_entry

            # Record the latest sequence number and persist it
            self.sequence_number_map[hash_of_payload] = StorageMapValue(
                sequence_nr=updated_entry.sequence_number,
                time_stamp=self.clock.millis(),
            )
            self.request_persistence()

            # Always broadcast refreshes
            self.broadcaster.broadcast(refresh_ttl_message, sender)

        except Exception as e:
            logger.error(f"refreshTTL failed, missing data: {str(e)}", exc_info=e)
            return False

        return True

    def remove(
        self,
        protected_storage_entry: "ProtectedStorageEntry",
        sender: Optional["NodeAddress"],
    ) -> bool:
        """
        Removes a ProtectedStorageEntry from the local P2P data storage. If it is successful, it will broadcast that
        change to the P2P network.

        Args:
            protected_storage_entry: ProtectedStorageEntry to add to the network
            sender: local NodeAddress, if available

        Returns:
            bool: True if the ProtectedStorageEntry was removed from the local P2P data storage and broadcast
        """
        protected_storage_payload = protected_storage_entry.protected_storage_payload
        hash_of_payload = StorageByteArray(get_32_byte_hash(protected_storage_payload))

        # If we have seen a more recent operation for this payload, ignore this one
        if not self.has_sequence_nr_increased(
            protected_storage_entry.sequence_number, hash_of_payload
        ):
            return False

        # Verify the ProtectedStorageEntry is well formed and valid for the remove operation
        if not protected_storage_entry.is_valid_for_remove_operation():
            return False

        # If we have already seen an Entry with the same hash, verify the metadata is the same
        stored_entry = self.map.get(hash_of_payload)
        if (
            stored_entry is not None
            and not protected_storage_entry.matches_relevant_pub_key(stored_entry)
        ):
            return False

        # Record the latest sequence number and persist it
        self.sequence_number_map[hash_of_payload] = StorageMapValue(
            sequence_nr=protected_storage_entry.sequence_number,
            time_stamp=self.clock.millis(),
        )
        self.request_persistence()

        # Update that we have seen this AddOncePayload so the next time it is seen it fails verification
        if isinstance(protected_storage_payload, AddOncePayload):
            self.removed_payloads_service.add_hash(hash_of_payload)

        if stored_entry is not None:
            # Valid remove entry, do the remove and signal listeners
            self.remove_from_map_and_data_store(
                [(hash_of_payload, protected_storage_entry)]
            )
        # else:
        #     # This means the RemoveData or RemoveMailboxData was seen prior to the AddData. We have already updated
        #     # the SequenceNumberMap appropriately so the stale Add will not pass validation, but we still want to
        #     # broadcast the remove to peers so they can update their state appropriately

        self.print_data("after remove")

        if isinstance(protected_storage_entry, ProtectedMailboxStorageEntry):
            self.broadcaster.broadcast(
                RemoveMailboxDataMessage(
                    protected_mailbox_storage_entry=protected_storage_entry
                ),
                sender,
            )
        else:
            self.broadcaster.broadcast(
                RemoveDataMessage(protected_storage_entry=protected_storage_entry),
                sender,
            )

        return True

    def get_protected_storage_entry(
        self,
        protected_storage_payload: "ProtectedStoragePayload",
        owner_storage_pub_key: "KeyPair",
    ) -> "ProtectedStorageEntry":
        hash_of_data = StorageByteArray(get_32_byte_hash(protected_storage_payload))

        if hash_of_data in self.sequence_number_map:
            sequence_number = self.sequence_number_map[hash_of_data].sequence_nr + 1
        else:
            sequence_number = 1

        hash_of_data_and_seq_nr = get_32_byte_hash(
            DataAndSeqNrPair(
                protected_storage_payload=protected_storage_payload,
                sequence_number=sequence_number,
            )
        )
        signature = Sig.sign(owner_storage_pub_key.private_key, hash_of_data_and_seq_nr)

        return ProtectedStorageEntry(
            protected_storage_payload=protected_storage_payload,
            owner_pub_key=owner_storage_pub_key.public_key,
            sequence_number=sequence_number,
            signature=signature,
            clock=self.clock,
        )

    def get_refresh_ttl_message(
        self,
        protected_storage_payload: "ProtectedStoragePayload",
        owner_storage_pub_key: "KeyPair",
    ) -> "RefreshOfferMessage":
        hash_of_payload = StorageByteArray(get_32_byte_hash(protected_storage_payload))

        if hash_of_payload in self.sequence_number_map:
            sequence_number = self.sequence_number_map[hash_of_payload].sequence_nr + 1
        else:
            sequence_number = 1

        hash_of_data_and_seq_nr = get_32_byte_hash(
            DataAndSeqNrPair(
                protected_storage_payload=protected_storage_payload,
                sequence_number=sequence_number,
            )
        )
        signature = Sig.sign(owner_storage_pub_key.private_key, hash_of_data_and_seq_nr)

        return RefreshOfferMessage(
            hash_of_data_and_seq_nr=hash_of_data_and_seq_nr,
            signature=signature,
            hash_of_payload=hash_of_payload.bytes,
            sequence_number=sequence_number,
        )

    def get_mailbox_data_with_signed_seq_nr(
        self,
        expirable_mailbox_storage_payload: "MailboxStoragePayload",
        storage_signature_pub_key: "KeyPair",
        receivers_public_key: "DSA.DsaKey",
    ) -> "ProtectedMailboxStorageEntry":
        hash_of_data = StorageByteArray(
            get_32_byte_hash(expirable_mailbox_storage_payload)
        )

        if hash_of_data in self.sequence_number_map:
            sequence_number = self.sequence_number_map[hash_of_data].sequence_nr + 1
        else:
            sequence_number = 1

        hash_of_data_and_seq_nr = get_32_byte_hash(
            DataAndSeqNrPair(
                protected_storage_payload=expirable_mailbox_storage_payload,
                sequence_number=sequence_number,
            )
        )
        signature = Sig.sign(
            storage_signature_pub_key.private_key, hash_of_data_and_seq_nr
        )

        return ProtectedMailboxStorageEntry(
            mailbox_storage_payload=expirable_mailbox_storage_payload,
            owner_pub_key=storage_signature_pub_key.public_key,
            sequence_number=sequence_number,
            signature=signature,
            receivers_pub_key=receivers_public_key,
            clock=self.clock,
        )

    def add_hash_map_changed_listener(
        self, hash_map_changed_listener: "HashMapChangedListener"
    ):
        self.hash_map_changed_listeners.add(hash_map_changed_listener)

    def remove_hash_map_changed_listener(
        self, hash_map_changed_listener: "HashMapChangedListener"
    ):
        self.hash_map_changed_listeners.discard(hash_map_changed_listener)

    def add_append_only_data_store_listener(
        self, listener: "AppendOnlyDataStoreListener"
    ):
        self.append_only_data_store_listeners.add(listener)

    def remove_append_only_data_store_listener(
        self, listener: "AppendOnlyDataStoreListener"
    ):
        self.append_only_data_store_listeners.discard(listener)

    ########################################################################################

    def remove_from_map_and_data_store(
        self,
        entries_to_remove: list[tuple["StorageByteArray", "ProtectedStorageEntry"]],
    ):
        if not entries_to_remove:
            return

        removed_protected_storage_entries = []

        for hash_of_payload, protected_storage_entry in entries_to_remove:
            # logger.trace("## removeFromMapAndDataStore: hashOfPayload={hash_of_payload}, map before remove={self.print_map()}")
            self.map.remove(hash_of_payload)  # Remove if exists
            # logger.trace("## removeFromMapAndDataStore: map after remove={self.print_map()}")

            # We inform listeners even if the entry was not found in our map
            removed_protected_storage_entries.append(protected_storage_entry)

            protected_storage_payload = (
                protected_storage_entry.protected_storage_payload
            )
            if isinstance(protected_storage_payload, PersistablePayload):
                previous = self.protected_data_store_service.remove(
                    hash_of_payload, protected_storage_entry
                )
                if previous is None:
                    logger.warning(
                        "We cannot remove the protectedStorageEntry from the protectedDataStoreService as it does not exist."
                    )

        for listener in self.hash_map_changed_listeners:
            listener.on_removed(removed_protected_storage_entries)

    def has_sequence_nr_increased(
        self, new_sequence_number: int, hash_of_data: "StorageByteArray"
    ) -> bool:
        if hash_of_data in self.sequence_number_map:
            stored_sequence_number = self.sequence_number_map[hash_of_data].sequence_nr
            if new_sequence_number > stored_sequence_number:
                # logger.debug(f"Sequence number has increased (>). sequenceNumber = {new_sequence_number} / "
                #            f"storedSequenceNumber={stored_sequence_number} / hashOfData={hash_of_data}")
                return True
            elif new_sequence_number == stored_sequence_number:
                if new_sequence_number == 0:
                    logger.debug(
                        "Sequence number is equal to the stored one and both are 0. "
                        "That is expected for network_messages which never got updated (mailbox msg)."
                    )
                else:
                    logger.debug(
                        f"Sequence number is equal to the stored one. sequenceNumber = {new_sequence_number} / "
                        f"storedSequenceNumber={stored_sequence_number}"
                    )
                return False
            else:
                logger.debug(
                    f"Sequence number is invalid. sequenceNumber = {new_sequence_number} / "
                    f"storedSequenceNumber={stored_sequence_number}. That can happen if the data owner gets "
                    "an old delayed data storage message."
                )
                return False
        else:
            return True

    def request_persistence(self):
        """Request persistence of the current state"""
        self.persistence_manager.request_persistence()

    def get_purged_sequence_number_map(
        self, persisted: dict["StorageByteArray", "StorageMapValue"]
    ) -> dict["StorageByteArray", "StorageMapValue"]:
        """Get a new map with entries older than PURGE_AGE_DAYS purged from the given map."""
        purged = {}
        max_age_ts = self.clock.millis() - int(
            timedelta(days=P2PDataStorage.PURGE_AGE_DAYS).total_seconds() * 1000
        )

        for key, value in persisted.items():
            if value.time_stamp > max_age_ts:
                purged[key] = value

        return purged

    def print_data(self, info: str):
        """Print debug info about the current data set."""
        if logger.isEnabledFor(logging.TRACE):
            sb = ["\n\n------------------------------------------------------------\n"]
            sb.append(f"Data set {info} operation")

            # We print the items sorted by hash with the payload class name and id
            temp_list: list[tuple[str, "ProtectedStorageEntry"]] = []
            for entry in self.map.values():
                hash_hex = StorageByteArray(
                    get_32_byte_hash(entry.protected_storage_payload)
                ).get_hex()
                temp_list.append((hash_hex, entry))

            temp_list.sort(key=lambda x: x[0])

            for hash_hex, storage_entry in temp_list:
                protected_storage_payload = storage_entry.protected_storage_payload
                hash_bytes = StorageByteArray(
                    get_32_byte_hash(protected_storage_payload)
                )
                map_value = self.sequence_number_map[hash_bytes]

                sb.append(f"\nHash={hash_hex}; ")
                sb.append(f"Class={protected_storage_payload.__class__.__name__}; ")
                sb.append(
                    f"SequenceNumbers (Object/Stored)={storage_entry.sequence_number} / "
                )
                sb.append(f"{map_value.sequence_nr if map_value else 'null'}; ")
                sb.append(
                    f"TimeStamp (Object/Stored)={storage_entry.creation_time_stamp} / "
                )
                sb.append(f"{map_value.time_stamp if map_value else 'null'}; ")
                sb.append(f"Payload={to_truncated_string(protected_storage_payload)}")

            sb.append(
                "\n------------------------------------------------------------\n"
            )
            logger.debug("".join(sb))

    def print_map(self) -> str:
        """Print debug info about the current map entries."""
        entries = []
        for key, value in self.map.items():
            hash_hex = key.get_hex()
            class_name = value.protected_storage_payload.__class__.__name__
            entries.append(f"{hash_hex}: {class_name}")
        return f"[{', '.join(entries)}]"

    def print_persistable_network_payload_map(
        self, map_obj: dict["StorageByteArray", "PersistableNetworkPayload"]
    ) -> str:
        """Print debug info about a PersistableNetworkPayload map."""
        entries = []
        for key, value in map_obj.items():
            hash_hex = key.get_hex()
            class_name = value.__class__.__name__
            entries.append(f"{hash_hex}: {class_name}")
        return f"[{', '.join(entries)}]"
