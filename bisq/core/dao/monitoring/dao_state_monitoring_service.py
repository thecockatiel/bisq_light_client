from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
import random
from typing import TYPE_CHECKING, Optional
from bisq.common.config.config import Config
from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bisq.common.file.file_util import remove_and_backup_file
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.monitoring.model.dao_state_block import DaoStateBlock
from bisq.core.dao.monitoring.model.dao_state_hash import DaoStateHash
from bisq.core.dao.monitoring.model.utxo_mismatch import UtxoMismatch
from bisq.core.dao.monitoring.network.checkpoint import Checkpoint
from bisq.core.dao.monitoring.network.dao_state_network_service import (
    DaoStateNetworkService,
)
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.dao.state.model.governance.issuance_type import IssuanceType
from utils.concurrency import ThreadSafeSet
from utils.data import ObservableList
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.dao.monitoring.network.state_network_service import (
        StateNetworkService,
    )
    from bisq.core.dao.monitoring.network.messages.get_dao_state_hashes_request import (
        GetDaoStateHashesRequest,
    )
    from bisq.core.dao.monitoring.network.messages.new_dao_state_hash_message import (
        NewDaoStateHashMessage,
    )
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.dao.state.model.blockchain.block import Block
    from bisq.core.network.p2p.seed.seed_node_repository import SeedNodeRepository
    from bisq.core.user.preferences import Preferences
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.genesis_tx_info import GenesisTxInfo
    from bisq.core.network.p2p.network.connection import Connection

logger = get_logger(__name__)


class DaoStateMonitoringService(
    DaoSetupService,
    DaoStateListener,
    DaoStateNetworkService.Listener[
        "NewDaoStateHashMessage", "GetDaoStateHashesRequest", "DaoStateHash"
    ],
):

    class Listener:
        def on_dao_state_hashes_changed(self):
            pass

        def on_checkpoint_fail(self):
            pass

        def on_dao_state_block_created(self):
            pass

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        dao_state_network_service: "DaoStateNetworkService",
        genesis_tx_info: "GenesisTxInfo",
        seed_node_repository: "SeedNodeRepository",
        preferences: "Preferences",
        storage_dir: Path,
        ignore_dev_msg: bool,
    ):
        self.dao_state_service = dao_state_service
        self._dao_state_network_service = dao_state_network_service
        self.genesis_tx_info = genesis_tx_info
        self.preferences = preferences
        self.storage_dir = storage_dir
        self.ignore_dev_msg = ignore_dev_msg

        self.dao_state_block_chain: list["DaoStateBlock"] = []
        self.dao_state_hash_chain: list["DaoStateHash"] = []
        self._listeners = ThreadSafeSet["DaoStateMonitoringService.Listener"]()
        self._parse_block_chain_complete = False
        self.is_in_conflict_with_non_seed_node = False
        self.is_in_conflict_with_seed_node = False
        self.dao_state_block_chain_not_connecting = False
        self.utxo_mismatches = ObservableList["UtxoMismatch"]()

        self._checkpoints = [
            # NOTE: investigate later
            Checkpoint(
                586920, bytes.fromhex("523aaad4e760f6ac6196fec1b3ec9a2f42e5b272")
            )
        ]
        self._checkpoint_failed = False
        self._num_calls = 0
        self._accumulated_duration = 0
        self.create_snapshot_handler: Optional[Callable[[], None]] = None
        self._dao_state_block_by_height = dict[int, "DaoStateBlock"]()

        self.seed_node_addresses = {
            node_address.get_full_address()
            for node_address in seed_node_repository.get_seed_node_addresses()
        }

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        self.dao_state_service.add_dao_state_listener(self)
        self._dao_state_network_service.add_listener(self)

    def start(self):
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_parse_block_chain_complete(self):
        self._parse_block_chain_complete = True
        last_block = self.dao_state_service.last_block
        if last_block:
            self._check_utxos(last_block)

        self._dao_state_network_service.add_listeners()

        # We take either the height of the previous hashBlock we have or 10 blocks below the chain tip.
        next_block_height = (
            self.genesis_tx_info.genesis_block_height
            if not self.dao_state_block_chain
            else self.dao_state_block_chain[-1].height + 1
        )
        past_10 = self.dao_state_service.chain_height - 10
        from_height = min(next_block_height, past_10)
        self._dao_state_network_service.request_hashes_from_all_connected_seed_nodes(from_height)

        if not self.ignore_dev_msg:
            self._verify_checkpoints()

        logger.info(
            f"ParseBlockChainComplete: Accumulated updateHashChain() calls for {self._num_calls} block took {self._accumulated_duration} ms "
            f"({int(self._accumulated_duration / self._num_calls) if self._num_calls else 0} ms in average / block)"
        )

    def on_dao_state_changed(self, block: "Block"):
        # During syncing we do not call _check_utxos as it's a bit slow (about 4 ms, in Java impl.)
        if self._parse_block_chain_complete:
            self._check_utxos(block)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // StateNetworkService.Listener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_new_state_hash_message(
        self, new_state_hash_message: "NewDaoStateHashMessage", connection: "Connection"
    ):
        # Called when receiving NewDaoStateHashMessages from peers after a new block
        peers_dao_state_hash = new_state_hash_message.state_hash
        if peers_dao_state_hash.height <= self.dao_state_service.chain_height:
            self._put_in_peers_map_and_check_for_conflicts(
                self._get_peers_address(connection.peers_node_address),
                peers_dao_state_hash,
            )
            for listener in self._listeners:
                listener.on_dao_state_hashes_changed()

    def on_peers_state_hashes(
        self,
        state_hashes: list["DaoStateHash"],
        peers_node_address: Optional["NodeAddress"],
    ):
        # Called when receiving GetDaoStateHashesResponse from seed nodes
        self._process_peers_dao_state_hashes(state_hashes, peers_node_address)
        for listener in self._listeners:
            listener.on_dao_state_hashes_changed()
        if handler := self.create_snapshot_handler:
            # As we get called multiple times from hashes of diff. seed nodes we want to avoid to
            # call our handler multiple times.
            self.create_snapshot_handler = None
            handler()

    def on_get_state_hash_request(
        self,
        connection: "Connection",
        get_state_hash_request: "GetDaoStateHashesRequest",
    ):
        from_height = get_state_hash_request.height
        dao_state_hashes = [
            e for e in self.dao_state_hash_chain if e.height >= from_height
        ]
        self._dao_state_network_service.send_get_state_hashes_response(
            connection, get_state_hash_request.nonce, dao_state_hashes
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def create_hash_from_block(self, block: "Block"):
        self._create_dao_state_block(block)
        if self._parse_block_chain_complete:
            # We notify listeners only after batch processing to avoid performance issues at UI code
            for listener in self._listeners:
                listener.on_dao_state_hashes_changed()

    def request_hashes_from_genesis_block_height(self, peers_address: str):
        self._dao_state_network_service.request_hashes(
            self.genesis_tx_info.genesis_block_height, peers_address
        )

    def apply_snapshot(self, persisted_dao_state_hash_chain: list["DaoStateHash"]):
        # We could get a reset from a reorg, so we clear all and start over from the genesis block.
        self.dao_state_hash_chain.clear()
        self.dao_state_block_chain.clear()
        self._dao_state_block_by_height.clear()
        self._dao_state_network_service.reset()

        if persisted_dao_state_hash_chain:
            logger.info(
                f"Apply snapshot with {len(persisted_dao_state_hash_chain)} daoStateHashes. "
                f"Last daoStateHash={persisted_dao_state_hash_chain[-1]}"
            )

        self.dao_state_hash_chain.extend(persisted_dao_state_hash_chain)
        for dao_state_hash in persisted_dao_state_hash_chain:
            dao_state_block = DaoStateBlock(dao_state_hash)
            self.dao_state_block_chain.append(dao_state_block)
            self._dao_state_block_by_height[dao_state_hash.height] = dao_state_block

    def add_response_listener(
        self, response_listener: "StateNetworkService.ResponseListener"
    ):
        self._dao_state_network_service.add_response_listener(response_listener)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Listeners
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listener(self, listener: "DaoStateMonitoringService.Listener"):
        self._listeners.add(listener)

    def remove_listener(self, listener: "DaoStateMonitoringService.Listener"):
        self._listeners.discard(listener)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _create_dao_state_block(self, block: "Block") -> Optional["DaoStateBlock"]:
        ts = get_time_ms()
        prev_hash = bytes()
        height = block.height

        if not self.dao_state_block_chain:
            # Only at genesis we allow an empty prevHash
            if height == self.genesis_tx_info.genesis_block_height:
                prev_hash = bytes()
            else:
                logger.warning(
                    "DaoStateBlockchain is empty but we received the block which was not the genesis block. "
                    "We stop execution here."
                )
                self.dao_state_block_chain_not_connecting = True
                for listener in self._listeners:
                    listener.on_dao_state_hashes_changed()
                return None
        else:
            last = self.dao_state_block_chain[-1]
            height_of_last_block = last.height
            if height == height_of_last_block + 1:
                prev_hash = last.hash
            else:
                logger.warning(
                    f"New block must be 1 block above previous block. height={height}, "
                    f"daoStateBlockChain.getLast().getHeight()={height_of_last_block}"
                )
                self.dao_state_block_chain_not_connecting = True
                for listener in self._listeners:
                    listener.on_dao_state_hashes_changed()
                return None

        state_as_bytes = self.dao_state_service.get_serialized_state_for_hash_chain()
        # We include the prev. hash in our new hash so we can be sure that if one hash is matching all the past would
        # match as well.
        combined = prev_hash + state_as_bytes
        hash = get_sha256_ripemd160_hash(combined)

        my_dao_state_hash = DaoStateHash(height, hash, True)
        dao_state_block = DaoStateBlock(my_dao_state_hash)
        self.dao_state_block_chain.append(dao_state_block)
        self._dao_state_block_by_height[height] = dao_state_block
        self.dao_state_hash_chain.append(my_dao_state_hash)

        # We only broadcast after parsing of blockchain is complete
        if self._parse_block_chain_complete:
            # We delay broadcast to give peers enough time to have received the block.
            # Otherwise, they would ignore our data if received block is in future to their local blockchain.
            delay_in_sec = 5 + random.randint(0, 9)
            if Config.BASE_CURRENCY_NETWORK_VALUE.is_regtest():
                delay_in_sec = 1
            UserThread.run_after(
                lambda: self._dao_state_network_service.broadcast_my_state_hash(
                    my_dao_state_hash
                ),
                timedelta(seconds=delay_in_sec),
            )

        duration = get_time_ms() - ts
        # We don't want to spam the output. We log accumulated time after parsing is completed.
        logger.trace(f"updateHashChain for block {block.height} took {duration} ms")
        self._accumulated_duration += duration
        self._num_calls += 1
        for listener in self._listeners:
            listener.on_dao_state_block_created()
        return dao_state_block

    def _process_peers_dao_state_hashes(
        self,
        state_hashes: list["DaoStateHash"],
        peers_node_address: Optional["NodeAddress"],
    ):
        use_dao_monitor = self.preferences.is_use_full_mode_dao_monitor()
        for peers_hash in state_hashes:
            # If we do not add own hashes during initial parsing we fill the missing hashes from the peer and create
            # at the last block our own hash.
            height = peers_hash.height
            optional_dao_state_block = self._find_dao_state_block(height)

            if not use_dao_monitor and optional_dao_state_block is None:
                if self.dao_state_service.chain_height == height:
                    # At the most recent block we create our own hash
                    last_block = self.dao_state_service.last_block
                    if last_block:
                        optional_dao_state_block = self._create_dao_state_block(
                            last_block
                        )
                    else:
                        pass  # optional_dao_state_block = self._find_dao_state_block(height)

                else:
                    # Otherwise, we create a block from the peers daoStateHash
                    dao_state_hash = DaoStateHash(height, peers_hash.hash, False)
                    dao_state_block = DaoStateBlock(dao_state_hash)
                    self.dao_state_block_chain.append(dao_state_block)
                    self._dao_state_block_by_height[height] = dao_state_block
                    self.dao_state_hash_chain.append(dao_state_hash)
                    optional_dao_state_block = dao_state_block

            # In any case we add the peer to our peersMap and check for conflicts on the relevant daoStateBlock
            self._put_in_peers_map_and_check_for_conflicts(
                self._get_peers_address(peers_node_address),
                peers_hash,
                optional_dao_state_block,
            )

    def _put_in_peers_map_and_check_for_conflicts(
        self,
        peers_address: str,
        peers_hash: "DaoStateHash",
        optional_dao_state_block: Optional["DaoStateBlock"] = "__UNSET__",
    ):
        if optional_dao_state_block == "__UNSET__":
            optional_dao_state_block = self._find_dao_state_block(peers_hash.height)

        if optional_dao_state_block:
            optional_dao_state_block.put_in_peers_map(peers_address, peers_hash)
            self._check_for_hash_conflicts(
                peers_hash, peers_address, optional_dao_state_block
            )

    def _check_for_hash_conflicts(
        self,
        peers_dao_state_hash: "DaoStateHash",
        peers_node_address: str,
        dao_state_block: "DaoStateBlock",
    ):
        if dao_state_block.my_state_hash.has_equal_hash(peers_dao_state_hash):
            return

        dao_state_block.put_in_conflict_map(peers_node_address, peers_dao_state_hash)
        conflict_msg = (
            f"We received a block hash from peer {peers_node_address} which conflicts with our block hash.\n"
            f"my peersDaoStateHash={dao_state_block.my_state_hash}\n"
            f"peers peersDaoStateHash={peers_dao_state_hash}"
        )

        if self._is_seed_node(peers_node_address):
            self.is_in_conflict_with_seed_node = True
            logger.warning(f"Conflict with seed nodes: {conflict_msg}")
        else:
            self.is_in_conflict_with_non_seed_node = True
            logger.debug(f"Conflict with non-seed nodes: {conflict_msg}")

    def _check_utxos(self, block: "Block"):
        genesis_total_supply = self.dao_state_service.genesis_total_supply.value
        compensation_issuance = self.dao_state_service.get_total_issued_amount(
            IssuanceType.COMPENSATION
        )
        reimbursement_issuance = self.dao_state_service.get_total_issued_amount(
            IssuanceType.REIMBURSEMENT
        )
        total_amount_of_burnt_bsq = (
            self.dao_state_service.get_total_amount_of_burnt_bsq()
        )
        # confiscated funds are still in the utxo set
        sum_utxo = sum(
            tx_output.value
            for tx_output in self.dao_state_service.get_unspent_tx_output_map().values()
        )
        sum_bsq = (
            genesis_total_supply
            + compensation_issuance
            + reimbursement_issuance
            - total_amount_of_burnt_bsq
        )

        if sum_bsq != sum_utxo:
            self.utxo_mismatches.append(UtxoMismatch(block.height, sum_utxo, sum_bsq))

    def _verify_checkpoints(self):
        for checkpoint in self._checkpoints:
            for dao_state_hash in self.dao_state_hash_chain:
                if dao_state_hash.height == checkpoint.height:
                    if dao_state_hash.hash == checkpoint.hash:
                        logger.info(f"Passed checkpoint {checkpoint}")
                    else:
                        if self._checkpoint_failed:
                            return
                        self._checkpoint_failed = True
                        try:
                            # Delete state and stop
                            self._remove_file("DaoStateStore")
                            self._remove_file("BlindVoteStore")
                            self._remove_file("ProposalStore")
                            self._remove_file("TempProposalStore")

                            for listener in self._listeners:
                                listener.on_checkpoint_fail()
                            logger.error(f"Failed checkpoint {checkpoint}")
                        except Exception as e:
                            logger.error(str(e), exc_info=e)

    def _remove_file(self, store_name: str):
        current_time = get_time_ms()
        new_file_name = f"{store_name}_{current_time}"
        backup_dir_name = "out_of_sync_dao_data"
        corrupted = self.storage_dir.joinpath(store_name)
        try:
            if corrupted.exists():
                remove_and_backup_file(
                    self.storage_dir, corrupted, new_file_name, backup_dir_name
                )
        except Exception as e:
            logger.error(str(e), exc_info=e)

    def _is_seed_node(self, peers_node_address: str) -> bool:
        return peers_node_address in self.seed_node_addresses

    def _get_peers_address(self, peers_node_address: Optional["NodeAddress"]) -> str:
        return (
            peers_node_address.get_full_address()
            if peers_node_address
            else f"Unknown peer {random.randint(0, 10000)}"  # TODO is this correct way to handle things?
        )

    def _find_dao_state_block(self, height: int) -> Optional["DaoStateBlock"]:
        return self._dao_state_block_by_height.get(height, None)
