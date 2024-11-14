from typing import TYPE_CHECKING, Callable

from bisq.core.network.p2p.persistence.historical_data_store_service import HistoricalDataStoreService
from bisq.core.network.p2p.persistence.persistable_network_payload_store import PersistableNetworkPayloadStore
from bisq.core.network.p2p.storage.payload.persistable_network_payload import PersistableNetworkPayload
from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray

if TYPE_CHECKING:
    from bisq.core.network.p2p.persistence.map_store_service import MapStoreService


class AppendOnlyDataStoreService():
    """Used for PersistableNetworkPayload data which gets appended to a map storage."""
    
    def __init__(self) -> None:
        self.services: list["MapStoreService[PersistableNetworkPayloadStore[PersistableNetworkPayload], PersistableNetworkPayload]"] = []
        
    def add_service(self, service: "MapStoreService[PersistableNetworkPayloadStore[PersistableNetworkPayload], PersistableNetworkPayload]") -> None:
        self.services.append(service)
        
    def read_from_resources(self, postfix: str, complete_handler: Callable):
        if not self.services:
            complete_handler()
            return
        remaining = len(self.services)
        def _complete_handler():
            nonlocal remaining
            remaining -= 1
            if remaining == 0:
                complete_handler()
            
        for service in self.services:
            service.read_from_resources(postfix, _complete_handler)
            
    # Uses synchronous execution on the userThread. Only used by tests. The async methods should be used by app code.
    def read_from_resources_sync(self, postfix: str):
        for service in self.services:
            service.read_from_resources_sync(postfix)
    
    # NOTE: Maybe TODO: rename ?
    def get_map(self, payload: "PersistableNetworkPayload") -> dict["StorageByteArray", "PersistableNetworkPayload"]:
        service = self.find_service(payload)
        if service:
            if isinstance(service, HistoricalDataStoreService):
                service.get_map_of_all_data()
            else:
                return service.get_map(payload)
        else:
            return {}
        
        
    def put(self, hash_as_byte_array: "StorageByteArray", payload: "PersistableNetworkPayload") -> None:
        service = self.find_service(payload)
        if service: 
            service.put_if_absent(hash_as_byte_array, payload)
        return service is not None
    
    def find_service(self, payload: "PersistableNetworkPayload") -> "MapStoreService[PersistableNetworkPayloadStore[PersistableNetworkPayload], PersistableNetworkPayload]":
        return next((service for service in self.services if service.can_handle(payload)), None)