from abc import ABC
from pathlib import Path
from typing import Callable, Generic, TypeVar, Optional
import logging
import bisq.core.common.version as Version
from bisq.core.network.p2p.persistence.map_store_service import MapStoreService
from bisq.core.network.p2p.persistence.persistable_network_payload_store import PersistableNetworkPayloadStore
from bisq.core.network.p2p.storage.payload.persistable_network_payload import PersistableNetworkPayload
from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray
from utils.immutables import ImmutableMap

T = TypeVar(
    "T", bound=PersistableNetworkPayloadStore[PersistableNetworkPayload]
) 

class HistoricalDataStoreService(Generic[T], MapStoreService[T, PersistableNetworkPayload], ABC):
    """
    Manages historical data stores tagged with the release versions.
    New data is added to the default map in the store (live data). Historical data is created from resource files.
    For initial data requests we only use the live data as the users version is sent with the
    request so the responding (seed)node can figure out if we miss any of the historical data.
    """

    def __init__(self, storage_dir: "Path", persistence_manager: "PersistableNetworkPayload[T]"):
        super().__init__(storage_dir, persistence_manager)
        self.stores_by_version: ImmutableMap[str, "PersistableNetworkPayloadStore[PersistableNetworkPayload]"] = ImmutableMap()
        # Cache to avoid that we have to recreate the historical data at each request
        self.all_historical_payloads: ImmutableMap["StorageByteArray", "PersistableNetworkPayload"] = ImmutableMap()

    # We give back a map of our live map and all historical maps newer than the requested version.
    # If requestersVersion is null we return all historical data.
    def get_map_since_version(self, requesters_version: Optional[str]) -> dict["StorageByteArray", "PersistableNetworkPayload"]:
        """Return a map of live data and all historical maps newer than the requested version."""
        # We add all our live data
        result = dict(self.store.get_map())

        # If we have a store with a newer version than the requesters version we will add those as well.
        for store_version, store in self.stores_by_version.items():
            # Old nodes not sending the version will get delivered all data
            if requesters_version is None:
                logging.info("The requester did not send a version. This is expected for not updated nodes.")
                result.update(store.get_map())
                continue

            # Otherwise we only add data if the requesters version is older then
            # the version of the particular store.
            is_new_version = Version.is_new_version(store_version, requesters_version)
            details = (
                "As our historical store is a newer version we add the data to our result map."
                if is_new_version
                else "As the requester version is not older as our historical store we do not add the data to the result map."
            )
            logging.debug(
                f"The requester had version {requesters_version}. Our historical data store has version {store_version}.\n{details}"
            )
            
            if is_new_version:
                result.update(store.get_map())

        logging.info(f"We found {len(result)} entries since requesters version {requesters_version}")
        return result

    def get_map_of_live_data(self) -> dict["StorageByteArray", "PersistableNetworkPayload"]:
        return self.store.get_map()

    def get_map_of_all_data(self) -> dict["StorageByteArray", "PersistableNetworkPayload"]:
        result = dict(self.get_map_of_live_data())
        result.update(self.all_historical_payloads)
        return result

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // MapStoreService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_map(self) -> dict["StorageByteArray", "PersistableNetworkPayload"]:
        # TODO: Implement proper DevEnv equivalent for Python
        logging.error("HistoricalDataStoreService.get_map should not be used by domain "
                     "clients but rather the custom methods get_map_of_all_data, get_map_of_live_data "
                     "or get_map_since_version")
        return self.get_map_of_all_data()
    
    def any_map_contains_key(self, hash: "StorageByteArray") -> bool:
        """Check if any map (live or historical) contains the given key."""
        if hash in self.get_map_of_live_data():
            return True
        return hash in self.all_historical_payloads

    def put(self, hash: "StorageByteArray", payload: "PersistableNetworkPayload") -> None:
        if self.any_map_contains_key(hash):
            return

        self.get_map_of_live_data()[hash] = payload
        self.request_persistence()

    def put_if_absent(self, hash: "StorageByteArray", payload: "PersistableNetworkPayload") -> Optional["PersistableNetworkPayload"]:
        # We do not return the value from getMapOfLiveData().put as we checked before that it does not contain any value.
        # So it will be always null. We still keep the return type as we override the method from MapStoreService which
        # follow the Map.putIfAbsent signature.
        self.put(hash, payload)
        return None
    
    def read_from_resources(self, post_fix: str, complete_handler: Callable) -> None:
        def on_persisted(persisted):
            logging.debug(
                f"We have created the {self.get_file_name()} store for the live data and "
                f"filled it with {len(self.get_map_of_live_data())} entries from the persisted data."
            )

            # Now we add our historical data stores
            all_historical_payloads: dict["StorageByteArray", "PersistableNetworkPayload"] = {}
            stores_by_version: dict[str, "PersistableNetworkPayloadStore[PersistableNetworkPayload]"] = {}
            num_files = len(Version.HISTORICAL_RESOURCE_FILE_VERSION_TAGS)

            def process_version(version: str):
                def on_complete():
                    nonlocal num_files
                    num_files -= 1
                    if num_files == 0:
                        # At last iteration we set the immutable map
                        self.all_historical_payloads = ImmutableMap(all_historical_payloads)
                        self.stores_by_version = ImmutableMap(stores_by_version)
                        complete_handler()

                self.read_historical_store_from_resources(
                    version,
                    post_fix,
                    all_historical_payloads,
                    stores_by_version,
                    on_complete
                )

            for version in Version.HISTORICAL_RESOURCE_FILE_VERSION_TAGS:
                process_version(version)

        self.read_store(on_persisted)

    ###########################################################################################
    ###########################################################################################

    def read_historical_store_from_resources(
        self,
        version: str,
        post_fix: str,
        all_historical_payloads: dict,
        stores_by_version: dict,
        complete_handler: Callable
    ) -> None:
        file_name = f"{self.get_file_name()}_{version}"
        self.make_file_from_resource_file(file_name, post_fix)

        def on_persisted(persisted: "PersistableNetworkPayloadStore[PersistableNetworkPayload]"):
            stores_by_version[version] = persisted
            all_historical_payloads.update(persisted.get_map())
            logging.debug(f"We have read from {file_name} {len(persisted.get_map())} historical items.")
            self.prune_store(persisted, version)
            complete_handler()

        # If resource file does not exist we do not create a new store as it would never get filled
        self.persistence_manager.read_persisted(
            on_persisted,
            complete_handler,
            file_name=file_name
        )

    def prune_store(
        self,
        historical_store: "PersistableNetworkPayloadStore[PersistableNetworkPayload]",
        version: str
    ) -> None:
        map_of_live_data = self.get_map_of_live_data()
        pre_live = len(map_of_live_data)
        
        # Remove keys that exist in historical store
        for key in historical_store.get_map().keys():
            map_of_live_data.pop(key, None)
            
        post_live = len(map_of_live_data)
        
        if pre_live > post_live:
            logging.debug(
                f"We pruned data from our live data store which are already contained in the "
                f"historical data store with version {version}. The live map had {pre_live} "
                f"entries before pruning and has {post_live} entries afterwards."
            )
        else:
            logging.debug(f"No pruning from historical data store with version {version} was applied")
            
        self.request_persistence()

