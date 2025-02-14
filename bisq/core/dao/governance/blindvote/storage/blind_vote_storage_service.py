from pathlib import Path
from typing import TYPE_CHECKING
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.core.dao.governance.blindvote.storage.blind_vote_payload import (
    BlindVotePayload,
)
from bisq.core.network.p2p.persistence.map_store_service import MapStoreService
from bisq.core.dao.governance.blindvote.storage.blind_vote_store import BlindVoteStore

if TYPE_CHECKING:
    from bisq.common.persistence.persistence_manager import PersistenceManager
    from bisq.core.network.p2p.storage.payload.persistable_network_payload import (
        PersistableNetworkPayload,
    )


class BlindVoteStorageService(
    MapStoreService["BlindVoteStore", "PersistableNetworkPayload"]
):
    FILE_NAME = "BlindVoteStore"

    def __init__(
        self,
        storage_dir: Path,
        persistenceManager: "PersistenceManager[BlindVoteStore]",
    ):
        super().__init__(storage_dir, persistenceManager)
        # At startup it is true, so the data we receive from the seed node are not checked against the phase as we have
        # not started up the DAO domain at that moment.
        self.not_in_vote_reveal_phase = True

    def get_file_name(self):
        return BlindVoteStorageService.FILE_NAME

    def initialize_persistence_manager(self):
        self.persistence_manager.initialize(
            self.store, PersistenceManagerSource.NETWORK
        )

    def get_map(self):
        return self.store.get_map()

    def can_handle(self, payload: "PersistableNetworkPayload"):
        return isinstance(payload, BlindVotePayload) and self.not_in_vote_reveal_phase

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Protected
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def create_store(self):
        return BlindVoteStore()
