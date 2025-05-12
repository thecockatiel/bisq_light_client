from datetime import timedelta
from bisq.common.setup.log_setup import get_ctx_logger
import random
from typing import TYPE_CHECKING, Optional
from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bisq.common.user_thread import UserThread
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.governance.blindvote.my_blind_vote_list import MyBlindVoteList
from bisq.core.dao.monitoring.model.blind_vote_state_block import BlindVoteStateBlock
from bisq.core.dao.monitoring.model.blind_vote_state_hash import BlindVoteStateHash
from bisq.core.dao.monitoring.network.blind_vote_state_network_service import (
    BlindVoteStateNetworkService,
)
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.dao.state.model.governance.dao_phase import DaoPhase
from utils.concurrency import AtomicBoolean, ThreadSafeSet
from utils.java_compat import java_cmp_str
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.dao.monitoring.network.messages.get_blind_vote_state_hashes_request import (
        GetBlindVoteStateHashesRequest,
    )
    from bisq.core.dao.monitoring.network.messages.new_blind_vote_state_hash_message import (
        NewBlindVoteStateHashMessage,
    )
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.dao.state.model.blockchain.block import Block
    from bisq.core.network.p2p.seed.seed_node_repository import SeedNodeRepository
    from bisq.shared.preferences.preferences import Preferences
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.genesis_tx_info import GenesisTxInfo
    from bisq.core.network.p2p.network.connection import Connection
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.governance.blindvote.blind_vote_list_service import (
        BlindVoteListService,
    )


class BlindVoteStateMonitoringService(
    DaoSetupService,
    DaoStateListener,
    BlindVoteStateNetworkService.Listener[
        "NewBlindVoteStateHashMessage",
        "GetBlindVoteStateHashesRequest",
        "BlindVoteStateHash",
    ],
):
    """
    Monitors the BlindVote P2P network payloads with using a hash of a sorted list of BlindVotes from one cycle and
    make it accessible to the network so we can detect quickly if any consensus issue arises.
    We create that hash at the first block of the VoteReveal phase. There is one hash created per cycle.
    The hash contains the hash of the previous block so we can ensure the validity of the whole history by
    comparing the last block.

    We request the state from the connected seed nodes after batch processing of BSQ is complete as well as we start
    to listen for broadcast messages from our peers about dao state of new blocks.

    We do NOT persist that chain of hashes as there is only one per cycle and the performance costs are very low.
    """

    class Listener:
        def on_blind_vote_state_block_chain_changed(self_):
            pass

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        blind_vote_state_network_service: "BlindVoteStateNetworkService",
        genesis_tx_info: "GenesisTxInfo",
        period_service: "PeriodService",
        blind_vote_list_service: "BlindVoteListService",
        seed_node_repository: "SeedNodeRepository",
    ):
        self.logger = get_ctx_logger(__name__)
        self._dao_state_service = dao_state_service
        self._blind_vote_state_network_service = blind_vote_state_network_service
        self._genesis_tx_info = genesis_tx_info
        self._period_service = period_service
        self._blind_vote_list_service = blind_vote_list_service
        self._seed_node_addresses = {
            node.get_full_address()
            for node in seed_node_repository.get_seed_node_addresses()
        }

        self.blind_vote_state_block_chain = list["BlindVoteStateBlock"]()
        self.blind_vote_state_hash_chain = list["BlindVoteStateHash"]()
        self.listeners = ThreadSafeSet["BlindVoteStateMonitoringService.Listener"]()
        self.is_in_conflict_with_non_seed_node = False
        self.is_in_conflict_with_seed_node = False
        self.parse_block_chain_complete = False

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        self._dao_state_service.add_dao_state_listener(self)
        self._blind_vote_state_network_service.add_listener(self)

    def start(self):
        pass

    def shut_down(self):
        self._dao_state_service.remove_dao_state_listener(self)
        self._blind_vote_state_network_service.remove_listener(self)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_dao_state_changed(self, block: "Block"):
        block_height = block.height
        genesis_block_height = self._genesis_tx_info.genesis_block_height

        if (
            not self.blind_vote_state_block_chain
            and block_height > genesis_block_height
        ):
            # Takes about 150 ms for dao testnet data (java)
            ts = get_time_ms()
            for i in range(genesis_block_height, block_height):
                self._maybe_update_hash_chain(i)
            if self.blind_vote_state_block_chain:
                self.logger.info(
                    f"updateHashChain for {block_height - genesis_block_height} blocks took {get_time_ms() - ts} ms"
                )

        ts = get_time_ms()
        updated = self._maybe_update_hash_chain(block_height)
        if updated:
            self.logger.info(
                f"updateHashChain for block {block_height} took {get_time_ms() - ts} ms"
            )

    def on_parse_block_chain_complete(self):
        self.parse_block_chain_complete = True
        self._blind_vote_state_network_service.add_listeners()

        # We wait for processing messages until we have completed batch processing

        # We request data from last 5 cycles. We ignore possible duration changes done by voting.
        # period is arbitrary anyway...
        current_cycle = self._period_service.current_cycle
        assert current_cycle is not None, "current_cycle must not be None"
        from_height = max(
            self._genesis_tx_info.genesis_block_height,
            self._dao_state_service.chain_height - current_cycle.get_duration() * 5,
        )

        self._blind_vote_state_network_service.request_hashes_from_all_connected_seed_nodes(
            from_height
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // StateNetworkService.Listener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_new_state_hash_message(
        self,
        new_state_hash_message: "NewBlindVoteStateHashMessage",
        connection: "Connection",
    ):
        if (
            new_state_hash_message.state_hash.height
            <= self._dao_state_service.chain_height
        ):
            self._process_peers_blind_vote_state_hash(
                new_state_hash_message.state_hash,
                connection.peers_node_address,
                True,
            )

    def on_get_state_hash_request(
        self,
        connection: "Connection",
        get_state_hash_request: "GetBlindVoteStateHashesRequest",
    ):
        from_height = get_state_hash_request.height
        blind_vote_state_hashes = [
            block.my_state_hash
            for block in self.blind_vote_state_block_chain
            if block.height >= from_height
        ]
        self._blind_vote_state_network_service.send_get_state_hashes_response(
            connection, get_state_hash_request.nonce, blind_vote_state_hashes
        )

    def on_peers_state_hashes(
        self,
        state_hashes: list["BlindVoteStateHash"],
        peers_node_address: Optional["NodeAddress"],
    ):
        # TODO: why atomic boolean ?
        has_changed = AtomicBoolean(False)
        for dao_state_hash in state_hashes:
            changed = self._process_peers_blind_vote_state_hash(
                dao_state_hash, peers_node_address, False
            )
            if changed:
                has_changed.set(True)

        if has_changed.get():
            for listener in self.listeners:
                listener.on_blind_vote_state_block_chain_changed()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def request_hashes_from_genesis_block_height(self, peers_address: str):
        self._blind_vote_state_network_service.request_hashes(
            self._genesis_tx_info.genesis_block_height, peers_address
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Listeners
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listener(self, listener: "BlindVoteStateMonitoringService.Listener"):
        self.listeners.add(listener)

    def remove_listener(self, listener: "BlindVoteStateMonitoringService.Listener"):
        self.listeners.discard(listener)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _maybe_update_hash_chain(self, block_height: int) -> bool:
        # We use first block in blind vote phase to create the hash of our blindVotes. We prefer to wait as long as
        # possible to increase the chance that we have received all blindVotes.
        if not self._is_first_block_of_blind_vote_phase(block_height):
            return False

        cycle = self._period_service.get_cycle(block_height)
        if cycle:
            blind_votes = sorted(
                (
                    blind_vote
                    for blind_vote in self._blind_vote_list_service.get_confirmed_blind_votes()
                    if blind_vote.tx_id
                    and self._period_service.is_tx_in_phase_and_cycle(
                        blind_vote.tx_id, DaoPhase.Phase.BLIND_VOTE, block_height
                    )
                ),
                key=lambda blind_vote: java_cmp_str(blind_vote.tx_id),
            )

            # We use MyBlindVoteList to get the serialized bytes from the blindVotes list
            serialized_blind_votes = MyBlindVoteList(blind_votes).serialize_for_hash()

            if not self.blind_vote_state_block_chain:
                prev_hash = b""
            else:
                prev_hash = self.blind_vote_state_block_chain[-1].hash

            combined = prev_hash + serialized_blind_votes
            hash_value = get_sha256_ripemd160_hash(combined)
            my_blind_vote_state_hash = BlindVoteStateHash(
                block_height, hash_value, len(blind_votes)
            )
            blind_vote_state_block = BlindVoteStateBlock(my_blind_vote_state_hash)
            self.blind_vote_state_block_chain.append(blind_vote_state_block)
            self.blind_vote_state_hash_chain.append(my_blind_vote_state_hash)

            # We only broadcast after parsing of blockchain is complete
            if self.parse_block_chain_complete:
                # We notify listeners only after batch processing to avoid performance issues at UI code (not relevant in light client probably)
                for listener in self.listeners:
                    listener.on_blind_vote_state_block_chain_changed()

                # We delay broadcast to give peers enough time to have received the block.
                # Otherwise they would ignore our data if received block is in future to their local blockchain.
                delay_in_sec = 5 + random.randint(0, 10)
                UserThread.run_after(
                    lambda: self._blind_vote_state_network_service.broadcast_my_state_hash(
                        my_blind_vote_state_hash
                    ),
                    timedelta(seconds=delay_in_sec),
                )

        return True

    def _process_peers_blind_vote_state_hash(
        self,
        blind_vote_state_hash: "BlindVoteStateHash",
        peers_node_address: Optional["NodeAddress"],
        notify_listeners: bool,
    ) -> bool:
        # TODO: atomic booleans dont make much sense here, investigate
        # why its needed and remove if unnecessary
        changed = AtomicBoolean(False)
        in_conflict_with_non_seed_node = AtomicBoolean(
            self.is_in_conflict_with_non_seed_node
        )
        in_conflict_with_seed_node = AtomicBoolean(self.is_in_conflict_with_seed_node)
        conflict_msg = ""

        for state_block in self.blind_vote_state_block_chain:
            if state_block.height == blind_vote_state_hash.height:
                peers_node_address_as_string = (
                    peers_node_address.get_full_address()
                    if peers_node_address
                    else f"Unknown peer {random.randint(0, 10000)}"
                )
                state_block.put_in_peers_map(
                    peers_node_address_as_string, blind_vote_state_hash
                )
                if not state_block.my_state_hash.has_equal_hash(blind_vote_state_hash):
                    state_block.put_in_conflict_map(
                        peers_node_address_as_string, blind_vote_state_hash
                    )
                    if peers_node_address_as_string in self._seed_node_addresses:
                        in_conflict_with_seed_node.set(True)
                    else:
                        in_conflict_with_non_seed_node.set(True)
                    conflict_msg = (
                        f"We received a block hash from peer {peers_node_address_as_string} "
                        f"which conflicts with our block hash.\n"
                        f"my blindVoteStateHash={state_block.my_state_hash}\n"
                        f"peers blindVoteStateHash={blind_vote_state_hash}"
                    )
                changed.set(True)
                break

        self.is_in_conflict_with_non_seed_node = in_conflict_with_non_seed_node.get()
        self.is_in_conflict_with_seed_node = in_conflict_with_seed_node.get()

        if conflict_msg:
            if self.is_in_conflict_with_seed_node:
                self.logger.warning(f"Conflict with seed nodes: {conflict_msg}")
            elif self.is_in_conflict_with_non_seed_node:
                self.logger.info(f"Conflict with non-seed nodes: {conflict_msg}")

        if notify_listeners and changed.get():
            for listener in self.listeners:
                listener.on_blind_vote_state_block_chain_changed()

        return changed.get()

    def _is_first_block_of_blind_vote_phase(self, block_height: int) -> bool:
        return block_height == self._period_service.get_first_block_of_phase(
            block_height, DaoPhase.Phase.VOTE_REVEAL
        )
