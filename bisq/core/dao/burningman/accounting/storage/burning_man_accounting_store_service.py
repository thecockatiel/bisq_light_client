from collections.abc import Callable
from datetime import timedelta
from bisq.common.setup.log_setup import get_ctx_logger
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from bisq.common.file.file_util import delete_file_if_exists
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.persistence.store_service import StoreService
from utils.concurrency import AtomicBoolean
from bisq.core.dao.burningman.accounting.storage.burning_man_accounting_store import (
    BurningManAccountingStore,
)

if TYPE_CHECKING:
    from bisq.core.dao.burningman.accounting.blockchain.accounting_block import (
        AccountingBlock,
    )
    from bisq.common.persistence.persistence_manager import PersistenceManager
    from bisq.core.network.p2p.storage.persistence.resource_data_store_service import (
        ResourceDataStoreService,
    )


class BurningManAccountingStoreService(StoreService["BurningManAccountingStore"]):
    FILE_NAME = "BurningManAccountingStore_v3"

    def __init__(
        self,
        resource_data_store_service: "ResourceDataStoreService",
        storage_dir: Path,
        persistence_manager: "PersistenceManager[BurningManAccountingStore]",
    ):
        super().__init__(storage_dir, persistence_manager)
        self.logger = get_ctx_logger(__name__)
        self._remove_all_blocks_callled = AtomicBoolean(False)
        resource_data_store_service.add_service(self)

    def read_from_resources(self, post_fix: str, complete_handler: Callable[[], None]):
        super().read_from_resources(post_fix, complete_handler)

        def delete_old_files():
            try:
                # Delete old BurningManAccountingStore file which was missing some data.
                delete_file_if_exists(
                    self.storage_dir.joinpath("BurningManAccountingStore")
                )
                delete_file_if_exists(
                    self.storage_dir.joinpath("BurningManAccountingStore_v2")
                )
            except Exception as e:
                raise RuntimeError(e)

        UserThread.run_after(delete_old_files, timedelta(seconds=5))

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def request_persistence(self):
        self.persistence_manager.request_persistence()

    def add_if_new_block(self, block: "AccountingBlock"):
        if self._remove_all_blocks_callled.get():
            return
        self.store.add_if_new_block(block)
        self.request_persistence()

    def for_each_block(self, consumer: Callable[["AccountingBlock"], None]):
        self.store.for_each_block(consumer)

    def purge_last_ten_blocks(self):
        if self._remove_all_blocks_callled.get():
            return
        self.store.purge_last_ten_blocks()
        self.request_persistence()

    def remove_all_blocks(self, result_handler: Callable[[], None]):
        self._remove_all_blocks_callled.set(True)
        self.store.remove_all_blocks()
        self.persistence_manager.persist_now(result_handler)

    def delete_storage_file(self):
        try:
            delete_file_if_exists(
                self.storage_dir.joinpath(BurningManAccountingStoreService.FILE_NAME)
            )
        except Exception as e:
            self.logger.error(e, exc_info=e)

    def get_last_block(self) -> Optional["AccountingBlock"]:
        return self.store.get_last_block()

    def get_block_at_height(self, height: int) -> Optional["AccountingBlock"]:
        return self.store.get_block_at_height(height)

    def get_blocks_at_least_with_height(self, min_height: int):
        return self.store.get_blocks_at_least_with_height(min_height)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Protected
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def create_store(self) -> "BurningManAccountingStore":
        return BurningManAccountingStore([])

    def initialize_persistence_manager(self):
        self.persistence_manager.initialize(
            self.store, PersistenceManagerSource.NETWORK, self.get_file_name()
        )

    def get_file_name(self) -> str:
        return BurningManAccountingStoreService.FILE_NAME
