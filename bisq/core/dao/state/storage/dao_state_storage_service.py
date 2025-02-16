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
        self.store.release_memory()
        # NOTE: we don't know if python's gc needs help or not, so we don't call GC directly
        UserThread.execute(complete_handler)

    def shut_down(self):
        self._executor_service.shutdown()

    def read_from_resources(self, post_fix: str, complete_handler: Callable[[], None]):
        def task():
            current_thread().name = "copyBsqBlocksFromResources"
            self._bsq_blocks_storage_service.copy_from_resources(post_fix)

            super().read_from_resources(
                post_fix, lambda: self._executor_service.submit(inner_task)
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
                            logger.warning(
                                f"heightOfLastBlock {height_of_last_block} must match chainHeight {chain_height}"
                            )
                else:
                    block_list = self._bsq_blocks_storage_service.migrate_blocks(
                        dao_state_as_proto.blocks
                    )
                self._blocks.clear()
                self._blocks.extend(block_list)
            UserThread.execute(complete_handler)

        self._executor_service.submit(task)

    def get_persisted_bsq_state(self) -> DaoState:
        dao_state_as_proto = self.store.dao_state_as_proto
        if dao_state_as_proto is not None:
            ts = get_time_ms()
            dao_state = DaoState.from_proto(dao_state_as_proto, self._blocks)
            logger.info(
                "Deserializing DaoState with %d blocks took %d ms",
                len(dao_state.blocks),
                get_time_ms() - ts,
            )
            return dao_state
        return DaoState()

    def get_persisted_dao_state_hash_chain(self) -> list[DaoStateHash]:
        return self.store.dao_state_hash_chain

    def release_memory(self):
        self._blocks.clear()
        self.store.release_memory()
        # NOTE: we don't know if python's gc needs help or not, so we don't call GC directly

    def resync_dao_state_from_genesis(self, result_handler: Callable[[], None]):
        backup_dir_name = "out_of_sync_dao_data"
        try:
            self._remove_and_backup_dao_consensus_files(
                self._storage_dir, backup_dir_name
            )
        except Exception as e:
            logger.error(str(e))

        self.store.dao_state_as_proto = DaoState.get_bsq_state_clone_excluding_blocks(
            DaoState()
        )
        self.store.dao_state_hash_chain = []
        self.persistence_manager.persist_now(result_handler)
        self._bsq_blocks_storage_service.remove_blocks_directory()

    def resync_dao_state_from_resources(self, storage_dir: Path):
        # We delete all DAO consensus data and remove the daoState so it will rebuild from latest
        # resource files.
        backup_dir_name = "out_of_sync_dao_data"
        self._remove_and_backup_dao_consensus_files(storage_dir, backup_dir_name)

        new_file_name = f"DaoStateStore_{get_time_ms()}"
        remove_and_backup_file(
            storage_dir,
            storage_dir.joinpath("DaoStateStore"),
            new_file_name,
            backup_dir_name,
        )

        self._bsq_blocks_storage_service.remove_blocks_directory()

    def _remove_and_backup_dao_consensus_files(
        self, storage_dir: Path, backup_dir_name: str
    ):
        # We delete all DAO related data. Some will be rebuild from resources.
        current_time = get_time_ms()
        new_file_name = f"BlindVoteStore_{current_time}"
        remove_and_backup_file(
            storage_dir,
            storage_dir.joinpath("BlindVoteStore"),
            new_file_name,
            backup_dir_name,
        )

        new_file_name = f"ProposalStore_{current_time}"
        remove_and_backup_file(
            storage_dir,
            storage_dir.joinpath("ProposalStore"),
            new_file_name,
            backup_dir_name,
        )

        # We also need to remove ballot list as it contains the proposals as well. It will be recreated at resync
        new_file_name = f"BallotList_{current_time}"
        remove_and_backup_file(
            storage_dir,
            storage_dir.joinpath("BallotList"),
            new_file_name,
            backup_dir_name,
        )

        new_file_name = f"UnconfirmedBsqChangeOutputList_{current_time}"
        remove_and_backup_file(
            storage_dir,
            storage_dir.joinpath("UnconfirmedBsqChangeOutputList"),
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
