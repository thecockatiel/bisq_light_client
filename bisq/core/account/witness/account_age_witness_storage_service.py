
from pathlib import Path
from typing import TYPE_CHECKING
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.core.account.witness.account_age_witness_store import AccountAgeWitnessStore
from bisq.core.network.p2p.persistence.historical_data_store_service import T, HistoricalDataStoreService
from bisq.core.network.p2p.storage.payload.persistable_network_payload import PersistableNetworkPayload
from bisq.core.account.witness.account_age_witness import AccountAgeWitness

if TYPE_CHECKING:
    from bisq.common.persistence.persistence_manager import PersistenceManager

class AccountAgeWitnessStorageService(HistoricalDataStoreService[AccountAgeWitnessStore]):
    FILE_NAME = "AccountAgeWitnessStore"
    
    def __init__(self, storage_dir: Path, persistence_manager: "PersistenceManager[AccountAgeWitnessStore]"):
        super().__init__(storage_dir, persistence_manager)
        
    def get_file_name(self):
        return AccountAgeWitnessStorageService.FILE_NAME
    
    def initialize_persistence_manager(self):
        self.persistence_manager.initialize(self.store, PersistenceManagerSource.NETWORK)
        
    def can_handle(self, payload: "PersistableNetworkPayload") -> bool:
        return isinstance(payload, AccountAgeWitness)
    
    def create_store(self) -> AccountAgeWitnessStore:
        return AccountAgeWitnessStore()