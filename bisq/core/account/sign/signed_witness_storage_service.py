from pathlib import Path
from typing import TYPE_CHECKING
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.core.account.sign.signed_witness import SignedWitness
from bisq.core.account.sign.signed_witness_store import SignedWitnessStore
from bisq.core.network.p2p.persistence.map_store_service import MapStoreService
from bisq.core.network.p2p.storage.payload.persistable_network_payload import PersistableNetworkPayload

if TYPE_CHECKING:
    from bisq.common.persistence.persistence_manager import PersistenceManager

class SignedWitnessStorageService(MapStoreService[SignedWitnessStore, PersistableNetworkPayload]):
    FILE_NAME = "SignedWitnessStore"
    
    def __init__(self, storage_dir: Path, persistence_manager: "PersistenceManager[SignedWitnessStore]"):
        super().__init__(storage_dir, persistence_manager)
        
    def initialize_persistence_manager(self):
        self.persistence_manager.initialize(self.store, PersistenceManagerSource.NETWORK)
  
    def get_file_name(self):
        return SignedWitnessStorageService.FILE_NAME
    
    def get_map(self):
        return self.store.get_map()

    def can_handle(self, payload: "PersistableNetworkPayload") -> bool:
        return isinstance(payload, SignedWitness)
    
    def create_store(self) -> SignedWitnessStore:
        return SignedWitnessStore()