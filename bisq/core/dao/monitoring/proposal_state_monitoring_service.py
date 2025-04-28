from datetime import timedelta
from bisq.common.setup.log_setup import get_ctx_logger
import random
from typing import TYPE_CHECKING, Optional
from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bisq.common.user_thread import UserThread
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.governance.proposal.my_proposal_list import MyProposalList
from bisq.core.dao.monitoring.model.proposal_state_block import ProposalStateBlock
from bisq.core.dao.monitoring.model.proposal_state_hash import ProposalStateHash
from bisq.core.dao.monitoring.network.proposal_state_network_service import (
    ProposalStateNetworkService,
)
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.dao.state.model.governance.dao_phase import DaoPhase
from utils.concurrency import AtomicBoolean, ThreadSafeSet
from utils.java_compat import java_cmp_str
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.dao.monitoring.network.state_network_service import (
        StateNetworkService,
    )
    from bisq.core.dao.monitoring.network.messages.get_proposal_state_hashes_request import (
        GetProposalStateHashesRequest,
    )
    from bisq.core.dao.monitoring.network.messages.new_proposal_state_hash_message import (
        NewProposalStateHashMessage,
    )
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.dao.state.model.blockchain.block import Block
    from bisq.core.network.p2p.seed.seed_node_repository import SeedNodeRepository
    from bisq.core.user.preferences import Preferences
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.genesis_tx_info import GenesisTxInfo
    from bisq.core.network.p2p.network.connection import Connection
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.governance.proposal.proposal_service import ProposalService


class ProposalStateMonitoringService(
    DaoSetupService,
    DaoStateListener,
    ProposalStateNetworkService.Listener[
        "NewProposalStateHashMessage",
        "GetProposalStateHashesRequest",
        "ProposalStateHash",
    ],
):
    """
    Monitors the Proposal P2P network payloads with using a hash of a sorted list of Proposals from one cycle and
    make it accessible to the network so we can detect quickly if any consensus issue arises.
    We create that hash at the first block of the BlindVote phase. There is one hash created per cycle.
    The hash contains the hash of the previous block so we can ensure the validity of the whole history by
    comparing the last block.

    We request the state from the connected seed nodes after batch processing of BSQ is complete as well as we start
    to listen for broadcast messages from our peers about dao state of new blocks.

    We do NOT persist that chain of hashes as there is only one per cycle and the performance costs are very low.
    """

    class Listener:
        def on_proposal_state_block_chain_changed(self_):
            pass

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        proposal_state_network_service: "ProposalStateNetworkService",
        genesis_tx_info: "GenesisTxInfo",
        period_service: "PeriodService",
        proposal_service: "ProposalService",
        seed_node_repository: "SeedNodeRepository",
    ):
        self.logger = get_ctx_logger(__name__)
        self._dao_state_service = dao_state_service
        self._proposal_state_network_service = proposal_state_network_service
        self._genesis_tx_info = genesis_tx_info
        self._period_service = period_service
        self._proposal_service = proposal_service
        self._seed_node_addresses = {
            node.get_full_address()
            for node in seed_node_repository.get_seed_node_addresses()
        }

        self.proposal_state_block_chain = list["ProposalStateBlock"]()
        self.proposal_state_hash_chain = list["ProposalStateHash"]()
        self.listeners = ThreadSafeSet["ProposalStateMonitoringService.Listener"]()
        self.is_in_conflict_with_non_seed_node = False
        self.is_in_conflict_with_seed_node = False
        self.parse_block_chain_complete = False

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        self._dao_state_service.add_dao_state_listener(self)
        self._proposal_state_network_service.add_listener(self)

    def start(self):
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_dao_state_changed(self, block: "Block"):
        block_height = block.height
        genesis_block_height = self._genesis_tx_info.genesis_block_height

        hash_chain_updated = False
        if not self.proposal_state_block_chain and block_height > genesis_block_height:
            # Takes about 150 ms for dao testnet data (Java)
            ts = get_time_ms()
            for i in range(genesis_block_height, block_height):
                is_hash_chain_updated = self._maybe_update_hash_chain(i)
                if is_hash_chain_updated:
                    hash_chain_updated = True
            if hash_chain_updated:
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
        self._proposal_state_network_service.add_listeners()

        # We wait for processing messages until we have completed batch processing

        # We request data from last 5 cycles. We ignore possible duration changes done by voting.
        # period is arbitrary anyway...
        current_cycle = self._period_service.current_cycle
        assert current_cycle is not None, "current_cycle must not be None"
        from_height = max(
            self._genesis_tx_info.genesis_block_height,
            self._dao_state_service.chain_height - current_cycle.get_duration() * 5,
        )

        self._proposal_state_network_service.request_hashes_from_all_connected_seed_nodes(
            from_height
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // StateNetworkService.Listener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_new_state_hash_message(
        self,
        new_state_hash_message: "NewProposalStateHashMessage",
        connection: "Connection",
    ):
        if (
            new_state_hash_message.state_hash.height
            <= self._dao_state_service.chain_height
        ):
            self._process_peers_proposal_state_hash(
                new_state_hash_message.state_hash,
                connection.peers_node_address,
                True,
            )

    def on_get_state_hash_request(
        self,
        connection: "Connection",
        get_state_hash_request: "GetProposalStateHashesRequest",
    ):
        from_height = get_state_hash_request.height
        proposal_state_hashes = [
            block.my_state_hash
            for block in self.proposal_state_block_chain
            if block.height >= from_height
        ]
        self._proposal_state_network_service.send_get_state_hashes_response(
            connection, get_state_hash_request.nonce, proposal_state_hashes
        )

    def on_peers_state_hashes(
        self,
        state_hashes: list["ProposalStateHash"],
        peers_node_address: Optional["NodeAddress"],
    ):
        # TODO: why atomic boolean ?
        has_changed = AtomicBoolean(False)
        for dao_state_hash in state_hashes:
            changed = self._process_peers_proposal_state_hash(
                dao_state_hash, peers_node_address, False
            )
            if changed:
                has_changed.set(True)

        if has_changed.get():
            for listener in self.listeners:
                listener.on_proposal_state_block_chain_changed()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def request_hashes_from_genesis_block_height(self, peers_address: str):
        self._proposal_state_network_service.request_hashes(
            self._genesis_tx_info.genesis_block_height, peers_address
        )

    def add_response_listener(
        self, response_listener: "StateNetworkService.ResponseListener"
    ):
        self._proposal_state_network_service.add_response_listener(response_listener)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Listeners
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listener(self, listener: "ProposalStateMonitoringService.Listener"):
        self.listeners.add(listener)

    def remove_listener(self, listener: "ProposalStateMonitoringService.Listener"):
        self.listeners.discard(listener)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _maybe_update_hash_chain(self, block_height: int) -> bool:
        # We use first block in blind vote phase to create the hash of our proposals. We prefer to wait as long as
        # possible to increase the chance that we have received all proposals.
        if not self._is_first_block_of_blind_vote_phase(block_height):
            return False

        cycle = self._period_service.get_cycle(block_height)
        if cycle:
            proposals = sorted(
                (
                    proposal
                    for proposal in self._proposal_service.get_validated_proposals()
                    if proposal.tx_id
                    and self._period_service.is_tx_in_phase_and_cycle(
                        proposal.tx_id, DaoPhase.Phase.PROPOSAL, block_height
                    )
                ),
                key=lambda proposal: java_cmp_str(proposal.tx_id),
            )

            # We use MyProposalList to get the serialized bytes from the proposals list
            serialized_proposals = MyProposalList(proposals).serialize_for_hash()

            if not self.proposal_state_block_chain:
                prev_hash = b""
            else:
                prev_hash = self.proposal_state_block_chain[-1].hash

            combined = prev_hash + serialized_proposals
            hash_value = get_sha256_ripemd160_hash(combined)
            my_proposal_state_hash = ProposalStateHash(
                block_height, hash_value, len(proposals)
            )
            proposal_state_block = ProposalStateBlock(my_proposal_state_hash)
            self.proposal_state_block_chain.append(proposal_state_block)
            self.proposal_state_hash_chain.append(my_proposal_state_hash)

            # We only broadcast after parsing of blockchain is complete
            if self.parse_block_chain_complete:
                # We notify listeners only after batch processing to avoid performance issues at UI code (not relevant in light client probably)
                for listener in self.listeners:
                    listener.on_proposal_state_block_chain_changed()

                # We delay broadcast to give peers enough time to have received the block.
                # Otherwise they would ignore our data if received block is in future to their local blockchain.
                delay_in_sec = 5 + random.randint(0, 10)
                UserThread.run_after(
                    lambda: self._proposal_state_network_service.broadcast_my_state_hash(
                        my_proposal_state_hash
                    ),
                    timedelta(seconds=delay_in_sec),
                )

        return True

    def _process_peers_proposal_state_hash(
        self,
        proposal_state_hash: "ProposalStateHash",
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

        for state_block in self.proposal_state_block_chain:
            if state_block.height == proposal_state_hash.height:
                peers_node_address_as_string = (
                    peers_node_address.get_full_address()
                    if peers_node_address
                    else f"Unknown peer {random.randint(0, 10000)}"
                )
                state_block.put_in_peers_map(
                    peers_node_address_as_string, proposal_state_hash
                )
                if not state_block.my_state_hash.has_equal_hash(
                    proposal_state_hash
                ):
                    state_block.put_in_conflict_map(
                        peers_node_address_as_string, proposal_state_hash
                    )
                    if peers_node_address_as_string in self._seed_node_addresses:
                        in_conflict_with_seed_node.set(True)
                    else:
                        in_conflict_with_non_seed_node.set(True)
                    conflict_msg = (
                        f"We received a block hash from peer {peers_node_address_as_string} "
                        f"which conflicts with our block hash.\n"
                        f"my proposalStateHash={state_block.my_state_hash}\n"
                        f"peers proposalStateHash={proposal_state_hash}"
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
                listener.on_proposal_state_block_chain_changed()

        return changed.get()

    def _is_first_block_of_blind_vote_phase(self, block_height: int) -> bool:
        return block_height == self._period_service.get_first_block_of_phase(
            block_height, DaoPhase.Phase.BLIND_VOTE
        )
