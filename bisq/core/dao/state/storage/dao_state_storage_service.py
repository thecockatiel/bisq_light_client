from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import current_thread
from typing import TYPE_CHECKING, Optional
from bisq.common.file.file_util import remove_and_backup_file
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.dao.monitoring.model.dao_state_hash import DaoStateHash
from bisq.core.dao.state.model.dao_state import DaoState
from bisq.core.dao.state.storage.dao_state_store import DaoStateStore
from bisq.core.network.p2p.persistence.store_service import StoreService
import pb_pb2 as protobuf
from utils.time import get_time_ms


if TYPE_CHECKING:
    from bisq.core.network.p2p.storage.persistence.resource_data_store_service import (
        ResourceDataStoreService,
    )
    from bisq.common.persistence.persistence_manager import PersistenceManager
    from bisq.core.dao.state.model.blockchain.block import Block
    from bisq.core.dao.state.storage.bsq_block_storage_service import (
        BsqBlocksStorageService,
    )

logger = get_logger(__name__)


class DaoStateStorageService(StoreService["DaoStateStore"]):
    """Manages persistence of the daoState."""

    FILE_NAME = "DaoStateStore"

    def __init__(
        self,
        resource_data_store_service: "ResourceDataStoreService",
        bsq_blocks_storage_service: "BsqBlocksStorageService",
        storage_dir: Path,
        persistence_manager: "PersistenceManager[DaoStateStore]",
    ):
        super().__init__(storage_dir, persistence_manager)
        self._bsq_blocks_storage_service = bsq_blocks_storage_service
        self._storage_dir = storage_dir

        self._blocks: list["Block"] = []
        self._executor_service = ThreadPoolExecutor(max_workers=1)
        self._future: Optional[Future] = None

        resource_data_store_service.add_service(self)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_file_name(self):
        return DaoStateStorageService.FILE_NAME

    @property
    def chain_height_of_persisted_blocks(self) -> int:
        return self._bsq_blocks_storage_service.chain_height_of_persisted_blocks

    def request_persistence(
        self,
        dao_state_as_proto: protobuf.DaoState,
        blocks: list["Block"],
        dao_state_hash_chain: list[DaoStateHash],
        complete_handler: Callable[[], None],
    ):
        if dao_state_as_proto is None:
            complete_handler()
            return

        if self._future and not self._future.done():
            UserThread.run_after(
                lambda: self.request_persistence(
                    dao_state_as_proto, blocks, dao_state_hash_chain, complete_handler
                ),
                timedelta(seconds=2),
            )
            return

        def task():
            try:
                current_thread().name = "Write-blocks-and-DaoState"
                self._bsq_blocks_storage_service.persist_blocks(blocks)
                self.store.dao_state_as_proto = dao_state_as_proto
                self.store.dao_state_hash_chain = dao_state_hash_chain
                ts = get_time_ms()
                self.persistence_manager.persist_now(
                    lambda: self._on_persistence_complete(ts, complete_handler)
                )
            except Exception as e:
                logger.error(
                    "Exception at persisting BSQ blocks and DaoState", exc_info=e
                )

        self._future = self._executor_service.submit(task)

    def _on_persistence_complete(self, ts: int, complete_handler: Callable[[], None]):
        # After we have written to disk we remove the daoStateAsProto in the store to avoid that it stays in
        # memory there until the next persist call.
        logger.info(f"Persist daoState took {get_time_ms() - ts} ms")
        self.store.clear()
        # NOTE: we don't know if python's gc needs help or not, so we don't call GC directly
        UserThread.execute(complete_handler)

    def shut_down(self):
        self._executor_service.shutdown()

    def read_from_resources(self, post_fix: str, complete_handler: Callable[[], None]):
        def handle_error(f: Future):
            try:
                f.result()
            except Exception as e:
                logger.error("Error at readFromResources", exc_info=e)

        def task():
            current_thread().name = "copyBsqBlocksFromResources"
            self._bsq_blocks_storage_service.copy_from_resources(post_fix)

            super(DaoStateStorageService, self).read_from_resources(
                post_fix, lambda: self._executor_service.submit(inner_task).add_done_callback(handle_error)
            )

        def inner_task():
            current_thread().name = "Read-BsqBlocksStore"
            dao_state_as_proto = self.store.dao_state_as_proto
            if dao_state_as_proto is not None:
                if not dao_state_as_proto.blocks:
                    chain_height = dao_state_as_proto.chain_height
                    block_list = self._bsq_blocks_storage_service.read_blocks(
                        chain_height
                    )
                    if block_list:
                        height_of_last_block = block_list[-1].height
                        if height_of_last_block != chain_height:
                            logger.error(
                                "Error at readFromResources. "
                                "heightOfLastBlock not same as chainHeight.\n"
                                f"heightOfLastBlock={height_of_last_block}; chainHeight={chain_height}.\n"
                                "This error scenario is handled by DaoStateSnapshotService, "
                                "it will resync from resources & reboot"
                            )
                else:
                    block_list = self._bsq_blocks_storage_service.migrate_blocks(
                        dao_state_as_proto.blocks
                    )
                self._blocks.clear()
                self._blocks.extend(block_list)
            current_thread().name = "Read-BsqBlocksStore-idle"
            UserThread.execute(complete_handler)

        self._executor_service.submit(task).add_done_callback(handle_error)

    def get_persisted_bsq_state(self) -> DaoState:
        dao_state_as_proto = self.store.dao_state_as_proto
        if dao_state_as_proto is not None:
            ts = get_time_ms()
            dao_state = DaoState.from_proto(dao_state_as_proto, self._blocks)
            logger.info(
                f"Deserializing DaoState with {len(dao_state.blocks)} blocks took {get_time_ms() - ts} ms"
            )
            return dao_state
        return DaoState()

    def is_chain_height_matching_last_block_height(self) -> bool:
        persisted_dao_state = self.get_persisted_bsq_state()
        height_of_persisted_last_block = persisted_dao_state.last_block.height
        chain_height_of_persisted_dao_state = persisted_dao_state.chain_height
        is_matching = (
            height_of_persisted_last_block == chain_height_of_persisted_dao_state
        )
        if not is_matching:
            logger.warning(
                "heightOfPersistedLastBlock is not same as chainHeightOfPersistedDaoState.\n"
                f"heightOfPersistedLastBlock={height_of_persisted_last_block}; "
                f"chainHeightOfPersistedDaoState={chain_height_of_persisted_dao_state}"
            )
        return is_matching

    def get_persisted_dao_state_hash_chain(self) -> list[DaoStateHash]:
        return self.store.dao_state_hash_chain

    def release_memory(self):
        self._blocks.clear()
        self.store.clear()
        # NOTE: we don't know if python's gc needs help or not, so we don't call GC directly

    def resync_dao_state_from_genesis(self, result_handler: Callable[[], None]):
        try:
            self._remove_and_backup_dao_consensus_files(False)
            # We recreate the directory so that we don't fill the blocks after restart from resources
            # In copyFromResources we only check for the directory not the files inside.
            self._bsq_blocks_storage_service.make_blocks_directory()
        except Exception as e:
            logger.error(str(e))

        # Reset to empty DaoState and DaoStateHashChain
        self.store.dao_state_as_proto = DaoState.get_bsq_state_clone_excluding_blocks(
            DaoState()
        )
        self.store.dao_state_hash_chain = []
        self.persistence_manager.persist_now(result_handler)

    def remove_and_backup_all_dao_data(self):
        # We delete all DAO consensus data and remove the daoState and blocks, so it will rebuild from latest
        # resource files.
        self._remove_and_backup_dao_consensus_files(True)

    def _remove_and_backup_dao_consensus_files(
        self, remove_dao_state_store: bool
    ):
        # We delete all DAO related data. At re-start they will get rebuilt from resources.
        if remove_dao_state_store:
            self._remove_and_backup_file("DaoStateStore")
        self._remove_and_backup_file("BlindVoteStore")
        self._remove_and_backup_file("ProposalStore")
        # We also need to remove ballot list as it contains the proposals as well. It will be recreated at resync
        self._remove_and_backup_file("BallotList")
        self._remove_and_backup_file("UnconfirmedBsqChangeOutputList")
        self._remove_and_backup_file("TempProposalStore")
        self._remove_and_backup_file("BurningManAccountingStore_v3")
        self._bsq_blocks_storage_service.remove_blocks_directory()

    def _remove_and_backup_file(self, filename: str):
        backup_dir_name = "out_of_sync_dao_data"
        new_file_name = filename + "_" + str(get_time_ms())
        remove_and_backup_file(
            self._storage_dir,
            self._storage_dir.joinpath(filename),
            new_file_name,
            backup_dir_name,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Protected
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def create_store(self) -> DaoStateStore:
        return DaoStateStore(None, [])

    def initialize_persistence_manager(self):
        self.persistence_manager.initialize(
            self.store, PersistenceManagerSource.NETWORK
        )
