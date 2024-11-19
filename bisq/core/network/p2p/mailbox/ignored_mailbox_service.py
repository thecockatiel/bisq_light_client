from typing import Callable

from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.core.network.p2p.mailbox.ignored_mailbox_map import IgnoredMailboxMap
from bisq.core.network.p2p.storage.payload.mailbox_storage_payload import MailboxStoragePayload
from utils.time import get_time_ms
from bisq.common.persistence.persistence_manager import PersistenceManager

class IgnoredMailboxService(PersistedDataHost):
    """
    NOTE: Need to check this in python implementation, the following comment is from java implementation:
    We persist failed attempts to decrypt mailbox messages (expected if mailbox message was not addressed to us).
    This improves performance at processing mailbox messages.
    On a fast 4 core machine 1000 mailbox messages take about 1.5 second. At second start-up using the persisted data
    it only takes about 30 ms.
    """
    
    def __init__(self, persistence_manager: "PersistenceManager[IgnoredMailboxMap]") -> None:
        self.persistence_manager = persistence_manager
        self.ignored_mailbox_map = IgnoredMailboxMap()
        self.persistence_manager.initialize(self.ignored_mailbox_map, PersistenceManager.Source.PRIVATE_LOW_PRIO)

    def read_persisted(self, complete_handler: Callable[[], None]) -> None:
        def handle_persisted(persisted: IgnoredMailboxMap) -> None:
            # At each load we cleanup outdated entries
            expired_date = get_time_ms() - MailboxStoragePayload.TTL
            for uid, timestamp in persisted.data_map.items():
                if timestamp > expired_date:
                    self.ignored_mailbox_map.put(uid, timestamp)
            self.persistence_manager.request_persistence()
            complete_handler()

        self.persistence_manager.read_persisted(handle_persisted, complete_handler)

    def is_ignored(self, uid: str) -> bool:
        return self.ignored_mailbox_map.contains_key(uid)

    def ignore(self, uid: str, creation_time_stamp: int) -> None:
        self.ignored_mailbox_map.put(uid, creation_time_stamp)
        self.persistence_manager.request_persistence()
