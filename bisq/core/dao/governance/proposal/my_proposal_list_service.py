from collections.abc import Callable
from typing import TYPE_CHECKING
from bisq.common.app.dev_env import DevEnv
from bisq.common.config.config import Config
from bisq.common.handlers.error_message_handler import ErrorMessageHandler
from bisq.common.handlers.result_handler import ResultHandler
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.btc.exceptions.tx_broadcast_exception import TxBroadcastException
from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
from bisq.core.dao.governance.proposal.my_proposal_list import MyProposalList
from bisq.core.dao.governance.proposal.my_proposal_list_service_listener import (
    MyProposalListServiceListener,
)
from bisq.core.dao.governance.proposal.storage.temp.temp_proposal_payload import (
    TempProposalPayload,
)
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.dao.state.model.governance.dao_phase import DaoPhase
from utils.concurrency import ThreadSafeSet
from utils.data import SimplePropertyChangeEvent

if TYPE_CHECKING:
    from bisq.core.dao.state.model.governance.proposal import Proposal
    from bitcoinj.core.transaction import Transaction
    from bisq.common.crypto.pub_key_ring import PubKeyRing
    from bisq.common.persistence.persistence_manager import PersistenceManager
    from bisq.core.btc.wallet.wallets_manager import WalletsManager
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.network.p2p.p2p_service import P2PService


logger = get_logger(__name__)


class MyProposalListService(PersistedDataHost, DaoStateListener):
    """
    Publishes proposal tx and proposalPayload to p2p network.
    Allow removal of proposal if in proposal phase.
    Maintains myProposalList for own proposals.
    Triggers republishing of my proposals at startup.
    """

    def __init__(
        self,
        p2p_service: "P2PService",
        dao_state_service: "DaoStateService",
        period_service: "PeriodService",
        wallets_manager: "WalletsManager",
        persistence_manager: "PersistenceManager",
        pub_key_ring: "PubKeyRing",
    ):
        self.p2p_service = p2p_service
        self.dao_state_service = dao_state_service
        self.period_service = period_service
        self.wallets_manager = wallets_manager
        self.persistence_manager = persistence_manager

        self.signature_pub_key = pub_key_ring.signature_pub_key

        self.listeners = ThreadSafeSet["MyProposalListServiceListener"]()
        self.my_proposal_list = MyProposalList()

        self.persistence_manager.initialize(
            self.my_proposal_list, PersistenceManagerSource.PRIVATE
        )

        self.dao_state_service.add_dao_state_listener(self)
        self.p2p_service.num_connected_peers_property.add_listener(
            self.num_connected_peers_listener
        )

    def num_connected_peers_listener(self, e: SimplePropertyChangeEvent[int]):
        self._re_publish_my_proposals_once_well_connected()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PersistedDataHost
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def read_persisted(self, complete_handler: Callable[[], None]):
        def on_persisted_read(persisted: "MyProposalList"):
            self.my_proposal_list.set_all(persisted.list)
            for listener in self.listeners:
                listener.on_list_changed(self.list)
            complete_handler()

        self.persistence_manager.read_persisted(on_persisted_read, complete_handler)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_parse_block_chain_complete(self):
        self._re_publish_my_proposals_once_well_connected()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # Broadcast tx and publish proposal to P2P network
    def publish_tx_and_payload(
        self,
        proposal: "Proposal",
        transaction: "Transaction",
        result_handler: ResultHandler,
        error_message_handler: ErrorMessageHandler,
    ):
        class Listener(TxBroadcasterCallback):
            def on_success(self, tx: "Transaction"):
                logger.info(f"Proposal tx has been published. TxId={tx.get_tx_id()}")
                result_handler()

            def on_failure(self, exception: "TxBroadcastException"):
                error_message_handler(str(exception))

        self.wallets_manager.publish_and_commit_bsq_tx(
            transaction,
            proposal.get_tx_type(),
            Listener(),
        )

        # We prefer to not wait for the tx broadcast as if the tx broadcast would fail we still prefer to have our
        # proposal stored and broadcasted to the p2p network. The tx might get re-broadcasted at a restart and
        # in worst case if it does not succeed the proposal will be ignored anyway.
        # Inconsistently propagated payloads in the p2p network could have potentially worse effects.
        self._add_to_p2p_network_as_protected_data(proposal, error_message_handler)

        # Add to list
        if proposal not in self.list:
            self.my_proposal_list.append(proposal)
            for listener in self.listeners:
                listener.on_list_changed(self.list)
            self._request_persistence()

    def remove(self, proposal: "Proposal") -> bool:
        if self.can_remove_proposal(proposal):
            success = self.p2p_service.remove_data(
                TempProposalPayload(proposal, self.signature_pub_key)
            )
            if not success:
                logger.warning(
                    f"Removal of proposal from p2p network failed. proposal={proposal}"
                )

            if self.my_proposal_list.remove(proposal):
                for listener in self.listeners:
                    listener.on_list_changed(self.list)
                self._request_persistence()
            else:
                logger.warning(
                    "We called remove at a proposal which was not in our list"
                )
            return success
        else:
            msg = (
                "remove called with a proposal which is outside of the proposal phase."
            )
            DevEnv.log_error_and_throw_if_dev_mode(msg)
            return False

    def is_mine(self, proposal: "Proposal") -> bool:
        return proposal in self.list

    @property
    def list(self):
        return self.my_proposal_list.list

    def add_listener(self, listener: "MyProposalListServiceListener"):
        self.listeners.add(listener)

    def remove_listener(self, listener: "MyProposalListServiceListener"):
        self.listeners.discard(listener)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _add_to_p2p_network_as_protected_data(
        self, proposal: "Proposal", error_message_handler: ErrorMessageHandler
    ):
        success = self._add_to_p2p_network_as_protected_data(proposal)
        if success:
            logger.info(
                f"TempProposalPayload has been added to P2P network. ProposalTxId={proposal.tx_id}"
            )
        else:
            msg = f"Adding of proposal to P2P network failed. proposal={proposal}"
            logger.error(msg)
            error_message_handler(msg)

    def _add_to_p2p_network_as_protected_data(self, proposal: "Proposal") -> bool:
        return self.p2p_service.add_protected_storage_entry(
            TempProposalPayload(proposal, self.signature_pub_key)
        )

    def _re_publish_my_proposals_once_well_connected(self):
        # We republish at each startup at any block during the cycle. We filter anyway for valid blind votes
        # of that cycle so it is 1 blind vote getting rebroadcast at each startup to my neighbors.
        min_peers = 4 if Config.BASE_CURRENCY_NETWORK_VALUE.is_mainnet() else 1
        if (
            self.p2p_service.num_connected_peers >= min_peers
            and self.p2p_service.is_bootstrapped
        ) or Config.BASE_CURRENCY_NETWORK_VALUE.is_regtest():
            for proposal in self.my_proposal_list.list:
                if self.period_service.is_tx_in_phase_and_cycle(
                    proposal.tx_id,
                    DaoPhase.Phase.PROPOSAL,
                    self.period_service.chain_height,
                ):
                    self._add_to_p2p_network_as_protected_data(proposal)

            # We delay removal of listener as we call that inside listener itself.
            UserThread.execute(
                lambda: self.p2p_service.num_connected_peers.remove_listener(
                    self.num_connected_peers_listener
                )
            )

    def _request_persistence(self):
        self.persistence_manager.request_persistence()

    def can_remove_proposal(self, proposal: "Proposal") -> bool:
        in_proposal_phase = self.period_service.is_in_phase(
            self.dao_state_service.chain_height, DaoPhase.Phase.PROPOSAL
        )
        return self.is_mine(proposal) and in_proposal_phase
