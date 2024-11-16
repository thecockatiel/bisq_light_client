from typing import TYPE_CHECKING
from collections.abc import Callable

from utils.concurrency import AtomicInt

if TYPE_CHECKING:
    from bisq.common.protocol.persistable.persistable_envelope import PersistableEnvelope
    from bisq.core.network.p2p.persistence.store_service import StoreService 
 
class ResourceDataStoreService:
    """Used for handling data from resource files."""
    
    def __init__(self):
        self.services: list["StoreService[PersistableEnvelope]"] = []
    
    def add_service(self, service: "StoreService[PersistableEnvelope]"):
        self.services.append(service)
    
    def read_from_resources(self, post_fix: str, complete_handler: Callable[[], None]):
        if not self.services:
            complete_handler()
            return
            
        remaining = AtomicInt(len(self.services))
        
        def on_service_complete():
            nonlocal remaining
            remaining.decrement_and_get()
            if remaining.get() == 0:
                complete_handler()
        
        for service in self.services:
            service.read_from_resources(post_fix, on_service_complete)
    
    def read_from_resources_sync(self, post_fix: str):
        """Uses synchronous execution. Only used by tests. The async methods should be used by app code."""
        for service in self.services:
            service.read_from_resources_sync(post_fix)
