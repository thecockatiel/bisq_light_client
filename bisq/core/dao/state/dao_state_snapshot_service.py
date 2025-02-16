from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from bisq.common.user_thread import UserThread
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.core.trade.delayed_payout_address_provider import DelayedPayoutAddressProvider
import pb_pb2 as protobuf
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.dao.state.model.blockchain.block import Block
    from bisq.core.dao.monitoring.dao_state_monitoring_service import (
        DaoStateMonitoringService,
    )
    from bisq.core.dao.state.storage.dao_state_storage_service import (
        DaoStateStorageService,
    )
    from bisq.common.config.config import Config
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallets_setup import WalletsSetup
    from bisq.core.dao.monitoring.model.dao_state_hash import DaoStateHash
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.genesis_tx_info import GenesisTxInfo
    from bisq.core.user.preferences import Preferences

logger = get_logger(__name__)


class DaoStateSnapshotService(DaoSetupService, DaoStateListener):
    """
    Manages periodical snapshots of the DaoState.
    At startup we apply a snapshot if available.
    At each trigger height we persist the latest snapshot candidate and set the current daoState as new candidate.
    The trigger height is determined by the SNAPSHOT_GRID. The latest persisted snapshot is min. the height of
    SNAPSHOT_GRID old not less than 2 times the SNAPSHOT_GRID old.
    """

    SNAPSHOT_GRID = 20

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        genesis_tx_info: "GenesisTxInfo",
        dao_state_storage_service: "DaoStateStorageService",
        dao_state_monitoring_service: "DaoStateMonitoringService",
        wallets_setup: "WalletsSetup",
        bsq_wallet_service: "BsqWalletService",
        preferences: "Preferences",
        config: "Config",
    ):
        self._dao_state_service = dao_state_service
        self._genesis_tx_info = genesis_tx_info
        self._dao_state_storage_service = dao_state_storage_service
        self._dao_state_monitoring_service = dao_state_monitoring_service
        self._wallets_setup = wallets_setup
        self._bsq_wallet_service = bsq_wallet_service
        self._preferences = preferences
        self._config = config
        self._storage_dir = config.storage_dir

        self._dao_state_candidate: Optional[protobuf.DaoState] = None
        self._hash_chain_candidate: list["DaoStateHash"] = []
        self._blocks_candidate: list["Block"] = []
        self._snapshot_height: int = 0
        self._chain_height_of_last_apply_snapshot: int = 0
        self.dao_requires_restart_handler: Optional[Callable[[], None]] = None
        self._dao_requires_restart_handler_attempts: int = 0
        self._ready_for_persisting: bool = True
        self._is_parse_block_chain_complete: bool = False

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        self._dao_state_service.add_dao_state_listener(self)

    def start(self):
        pass

    def shut_down(self):
        self._dao_state_storage_service.shut_down()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_parse_block_complete_after_batch_processing(self, block: "Block"):
        if (
            self._config.base_currency_network.is_mainnet()
            and self._wallets_setup.is_download_complete
            and self._dao_state_service.chain_height
            == self._bsq_wallet_service.get_best_chain_height()
        ):
            # In case the DAO state is invalid we might get an outdated RECIPIENT_BTC_ADDRESS. In that case we trigger
            # a dao resync from resources.
            address = self._dao_state_service.get_param_value(
                Param.RECIPIENT_BTC_ADDRESS, self._dao_state_service.chain_height
            )
            if DelayedPayoutAddressProvider.is_outdated_address(address):
                logger.warning(
                    "The RECIPIENT_BTC_ADDRESS is not as expected. The DAO state is probably out of "
                    "sync and a resync should fix that issue."
                )
                self._resync_dao_state_from_resources()

    # We listen onDaoStateChanged to ensure the dao state has been processed from listener clients after parsing.
    # We need to listen during batch processing as well to write snapshots during that process.
    # NOTE: we removed GcUtil calls in python for now
    def on_dao_state_changed(self, block: "Block"):
        # If we have isUseDaoMonitor activated we apply the hash and snapshots at each new block during initial parsing.
        # Otherwise we do it only after the initial blockchain parsing is completed to not delay the parsing.
        # In that case we get the missing hashes from the seed nodes. At any new block we do the hash calculation
        # ourself and therefore get back confidence that our DAO state is in sync with the network.
        if (
            self._preferences.is_use_full_mode_dao_monitor()
            or self._is_parse_block_chain_complete
        ):
            # We need to execute first the daoStateMonitoringService.createHashFromBlock to get the hash created
            self._dao_state_monitoring_service.create_hash_from_block(block)
            self.maybe_create_snapshot(block)

    def on_parse_block_chain_complete(self):
        self._is_parse_block_chain_complete = True

        # In case we have dao monitoring deactivated we create the snapshot after we are completed with parsing
        # and we got called back from daoStateMonitoringService once the hashes are created from peers data.
        if not self._preferences.is_use_full_mode_dao_monitor():
            # We register a callback handler once the daoStateMonitoringService has received the missing hashes from
            # the seed node and applied the latest hash. After that we are ready to make a snapshot and persist it.
            self._dao_state_monitoring_service.create_snapshot_handler = (
                self._create_snapshot_after_parsing
            )

    def _create_snapshot_after_parsing(self):
        # As we did not have created any snapshots during initial parsing we create it now. We cannot use the past
        # snapshot height as we have not cloned a candidate (that would cause quite some delay during parsing).
        # The next snapshots will be created again according to the snapshot height grid (each 20 blocks).
        # This also comes with the improvement that the user does not need to load the past blocks back to the last
        # snapshot height. Though it comes also with the small risk that in case of re-orgs the user need to do
        # a resync in case the dao state would have been affected by that reorg.
        ts = get_time_ms()
        # We do not keep a copy of the clone as we use it immediately for persistence.
        chain_height = self._dao_state_service.chain_height
        logger.info(f"Create snapshot at height {chain_height}")
        # We do not keep the data in our fields to enable gc as soon its released in the store

        dao_state_for_snapshot = self._get_dao_state_for_snapshot()
        blocks_for_snapshot = self._get_blocks_for_snapshot()
        hash_chain_for_snapshot = self._get_hash_chain_for_snapshot()
        self._dao_state_storage_service.request_persistence(
            dao_state_for_snapshot,
            blocks_for_snapshot,
            hash_chain_for_snapshot,
            lambda: logger.info(
                f"Persisted daoState after parsing completed at height {chain_height}. Took {get_time_ms() - ts} ms"
            ),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # We need to process during batch processing as well to write snapshots during that process.
    def maybe_create_snapshot(self, block: "Block"):
        chain_height = block.height

        # Either we don't have a snapshot candidate yet, or if we have one the height at that snapshot candidate must be
        # different to our current height.
        no_snapshot_candidate_or_different_height = (
            self._dao_state_candidate is None or self._snapshot_height != chain_height
        )
        if (
            self._is_snapshot_height(chain_height)
            and self._dao_state_service.blocks
            and self._is_valid_height(
                self._dao_state_service.block_height_of_last_block
            )
            and no_snapshot_candidate_or_different_height
        ):

            # We protect to get called while we are not completed with persisting the daoState. This can take about
            # 20 seconds and it is not expected that we get triggered another snapshot event in that period, but this
            # check guards that we would skip such calls..
            if not self._ready_for_persisting:
                if self._preferences.is_use_full_mode_dao_monitor():
                    # In case we dont use isUseFullModeDaoMonitor we might called here too often as the parsing is much
                    # faster than the persistence and we likely create only 1 snapshot during initial parsing, so
                    # we log only if isUseFullModeDaoMonitor is true as then parsing is likely slower and we would
                    # expect that we do a snapshot at each trigger block.
                    logger.info(
                        "We try to persist a daoState but the previous call has not completed yet. "
                        "We ignore that call and skip that snapshot. "
                        "Snapshot will be created at next snapshot height again. This is not to be expected with live "
                        "blockchain data."
                    )
                return

            if self._dao_state_candidate is not None:
                self._persist()
            else:
                self._create_snapshot()

    def _persist(self):
        ts = get_time_ms()
        self._ready_for_persisting = False
        self._dao_state_storage_service.request_persistence(
            self._dao_state_candidate,
            self._blocks_candidate,
            self._hash_chain_candidate,
            lambda: (
                logger.info(
                    f"Serializing daoStateCandidate for writing to Disc at chainHeight {self._snapshot_height} took {get_time_ms() - ts} ms."
                ),
                self._create_snapshot(),
                setattr(self, "_ready_for_persisting", True),
            ),
        )

    def _create_snapshot(self):
        ts = get_time_ms()
        # Now we clone and keep it in memory for the next trigger event
        # We do not fit into the target grid of 20 blocks as we get called here once persistence is
        # done from the write thread (mapped back to user thread).
        # As we want to prevent to maintain 2 clones we prefer that strategy. If we would do the clone
        # after the persist call we would keep an additional copy in memory.
        self._dao_state_candidate = self._get_dao_state_for_snapshot()
        self._blocks_candidate = self._get_blocks_for_snapshot()
        self._hash_chain_candidate = self._get_hash_chain_for_snapshot()
        self._snapshot_height = self._dao_state_service.chain_height

        logger.info(
            f"Cloned new daoStateCandidate at height {self._snapshot_height} took {get_time_ms() - ts} ms."
        )

    def apply_snapshot(self, from_reorg: bool):
        persisted_bsq_state = (
            self._dao_state_storage_service.get_persisted_bsq_state()
        )  # TODO: sanity check: its never null
        persisted_dao_state_hash_chain = (
            self._dao_state_storage_service.get_persisted_dao_state_hash_chain()
        )
        if persisted_bsq_state:
            chain_height_of_persisted = persisted_bsq_state.chain_height
            if persisted_bsq_state.blocks:
                height_of_last_block = persisted_bsq_state.last_block.height
                if height_of_last_block != chain_height_of_persisted:
                    logger.warning(
                        "chain_height_of_persisted must be same as height_of_last_block"
                    )
                    self._resync_dao_state_from_resources()
                    return
                if self._is_valid_height(height_of_last_block):
                    if (
                        self._chain_height_of_last_apply_snapshot
                        != chain_height_of_persisted
                    ):
                        self._chain_height_of_last_apply_snapshot = (
                            chain_height_of_persisted
                        )
                        self._dao_state_service.apply_snapshot(persisted_bsq_state)
                        self._dao_state_monitoring_service.apply_snapshot(
                            persisted_dao_state_hash_chain
                        )
                        self._dao_state_storage_service.release_memory()
                    else:
                        # The reorg might have been caused by the previous parsing which might contains a range of
                        # blocks.
                        logger.warning(
                            f"We applied already a snapshot with chain_height {self._chain_height_of_last_apply_snapshot}. "
                            "We remove all dao store files and shutdown. After a restart resource files will "
                            "be applied if available."
                        )
                        self._resync_dao_state_from_resources()
            elif from_reorg:
                logger.info(
                    "We got a reorg and we want to apply the snapshot but it is empty. "
                    "That is expected in the first blocks until the first snapshot has been created. "
                    "We remove all dao store files and shutdown. "
                    "After a restart resource files will be applied if available."
                )
                self._resync_dao_state_from_resources()
            else:
                logger.info(
                    "No Bsq blocks in DaoState. Expected if no data are provided yet from resources or persisted data."
                )
        else:
            logger.info(
                "Try to apply snapshot but no stored snapshot available. That is expected at first blocks."
            )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _is_valid_height(self, height_of_last_block: int) -> bool:
        return height_of_last_block >= self._genesis_tx_info.genesis_block_height

    def _resync_dao_state_from_resources(self):
        logger.info("resync_dao_state_from_resources called")
        self._dao_requires_restart_handler_attempts += 1
        if (
            self.dao_requires_restart_handler is None
            and self._dao_requires_restart_handler_attempts <= 3
        ):
            logger.warning(
                "dao_requires_restart_handler has not been initialized yet, will try again in 10 seconds"
            )
            UserThread.run_after(
                self._resync_dao_state_from_resources,
                timedelta(seconds=10),  # a delay for the app to init
            )
            return
        try:
            self._dao_state_storage_service.resync_dao_state_from_resources(
                self._storage_dir
            )
            # the restart handler informs the user of the need to restart bisq (in desktop mode)
            if self.dao_requires_restart_handler is None:
                logger.error(
                    "dao_requires_restart_handler COULD NOT be called as it has not been initialized yet"
                )
            else:
                logger.info("calling dao_requires_restart_handler...")
                self.dao_requires_restart_handler()
        except Exception as e:
            logger.error(f"Error at resync_dao_state_from_resources: {e}")

    def _get_snapshot_height(self, genesis_height: int, height: int, grid: int) -> int:
        return round(max(genesis_height + 3 * grid, height) / grid) * grid - grid

    def _is_snapshot_height_internal(
        self, genesis_height: int, height: int, grid: int
    ) -> bool:
        return height % grid == 0 and height >= self._get_snapshot_height(
            genesis_height, height, grid
        )

    def _is_snapshot_height(self, height: int) -> bool:
        return self._is_snapshot_height_internal(
            self._genesis_tx_info.genesis_block_height,
            height,
            DaoStateSnapshotService.SNAPSHOT_GRID,
        )

    def _get_dao_state_for_snapshot(self) -> protobuf.DaoState:
        return self._dao_state_service.get_bsq_state_clone_excluding_blocks()

    def _get_blocks_for_snapshot(self) -> list["Block"]:
        from_block_height = (
            self._dao_state_storage_service.chain_height_of_persisted_blocks + 1
        )
        return self._dao_state_service.get_blocks_from_block_height(from_block_height)

    def _get_hash_chain_for_snapshot(self) -> list["DaoStateHash"]:
        return list(self._dao_state_monitoring_service.dao_state_hash_chain)
