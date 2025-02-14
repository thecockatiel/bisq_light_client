from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.core.dao.governance.proposal.storage.temp.temp_proposal_payload import (
    TempProposalPayload,
)
from bisq.core.dao.governance.proposal.storage.temp.temp_proposal_store import (
    TempProposalStore,
)
from bisq.core.network.p2p.persistence.map_store_service import MapStoreService

if TYPE_CHECKING:
    from bisq.common.persistence.persistence_manager import PersistenceManager
    from bisq.core.network.p2p.storage.payload.protected_storage_entry import (
        ProtectedStorageEntry,
    )


class TempProposalStorageService(
    MapStoreService["TempProposalStore", "ProtectedStorageEntry"]
):
    FILE_NAME = "TempProposalStore"

    def __init__(
        self,
        storage_dir: Path,
        persistence_manager: "PersistenceManager[TempProposalStore]",
    ):
        super().__init__(storage_dir, persistence_manager)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_file_name(self):
        return TempProposalStorageService.FILE_NAME

    def initialize_persistence_manager(self):
        self.persistence_manager.initialize(
            self.store, PersistenceManagerSource.NETWORK
        )

    def get_map(self):
        return self.store.map

    def can_handle(self, entry: "ProtectedStorageEntry"):
        return isinstance(entry.protected_storage_payload, TempProposalPayload)

    def read_from_resources(self, post_fix: str, complete_handler: Callable[[], None]):
        # We do not have a resource file for that store, so we just call the read_store method instead.
        self.read_store(lambda persisted: complete_handler())

    def create_store(self):
        return TempProposalStore()
