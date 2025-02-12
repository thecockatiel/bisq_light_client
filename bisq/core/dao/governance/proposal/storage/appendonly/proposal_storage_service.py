from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.core.dao.governance.proposal.storage.appendonly.proposal_payload import (
    ProposalPayload,
)
from bisq.core.dao.governance.proposal.storage.appendonly.proposal_store import (
    ProposalStore,
)
from bisq.core.network.p2p.persistence.map_store_service import MapStoreService
from bisq.core.network.p2p.storage.payload.persistable_network_payload import (
    PersistableNetworkPayload,
)


class ProposalStorageService(
    MapStoreService["ProposalStore", "PersistableNetworkPayload"]
):
    FILE_NAME = "ProposalStore"

    def get_file_name(self):
        return ProposalStorageService.FILE_NAME

    def initialize_persistence_manager(self):
        self.persistence_manager.initialize(
            self.store, PersistenceManagerSource.NETWORK
        )

    def get_map(self):
        return self.store.get_map()

    def can_handle(self, payload: "PersistableNetworkPayload"):
        return isinstance(payload, ProposalPayload)

    def create_store(self):
        return ProposalStore()
