from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING
from collections.abc import Callable
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.protocol.persistable.persistable_data_host import (
    PersistedDataHost,
)
from bisq.core.network.p2p.persistence.removed_payloads_map import RemovedPayloadsMap
from bisq.core.network.p2p.storage.payload.mailbox_storage_payload import (
    MailboxStoragePayload,
)
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray
    from bisq.common.persistence.persistence_manager import PersistenceManager


class RemovedPayloadsService(PersistedDataHost):
    """
    We persist the hashes and timestamp when a AddOncePayload payload got removed. This protects that it could be
    added again for instance if the sequence number map would be inconsistent/deleted or when we receive data from
    seed nodes where we do skip some checks.
    """

    def __init__(
        self,
        persistence_manager: "PersistenceManager[RemovedPayloadsMap]",
    ):
        self.logger = get_ctx_logger(__name__)
        self.persistence_manager = persistence_manager
        self.removed_payloads_map = RemovedPayloadsMap()

        self.persistence_manager.initialize(
            self.removed_payloads_map, PersistenceManagerSource.PRIVATE_LOW_PRIO
        )

    ###########################
    # PersistedDataHost
    ###########################

    def read_persisted(self, complete_handler: Callable[[], None]) -> None:
        cut_off_date = get_time_ms() - MailboxStoragePayload.TTL

        def on_persisted(persisted: RemovedPayloadsMap) -> None:
            for hash_key, date in persisted.date_by_hashes.items():
                if date > cut_off_date:
                    self.removed_payloads_map.date_by_hashes[hash_key] = date

            self.logger.trace(
                f"## read_persisted: removedPayloadsMap size={len(self.removed_payloads_map.date_by_hashes)}"
            )
            self.persistence_manager.request_persistence()
            complete_handler()

        self.persistence_manager.read_persisted(on_persisted, complete_handler)

    def was_removed(self, hash_of_payload: "StorageByteArray") -> bool:
        self.logger.trace(
            f"## called was_removed: hash_of_payload={hash_of_payload}, removed_payloads_map={self.removed_payloads_map}"
        )
        return hash_of_payload in self.removed_payloads_map.date_by_hashes

    def add_hash(self, hash_of_payload: "StorageByteArray") -> None:
        self.logger.trace(
            f"## called add_hash: hash_of_payload={hash_of_payload}, removed_payloads_map={self.removed_payloads_map}"
        )
        if hash_of_payload not in self.removed_payloads_map.date_by_hashes:
            self.removed_payloads_map.date_by_hashes[hash_of_payload] = get_time_ms()
        self.persistence_manager.request_persistence()
