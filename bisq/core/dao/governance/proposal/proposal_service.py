from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING, Collection, Iterable
from bisq.core.dao.governance.proposal.storage.temp.temp_proposal_payload import (
    TempProposalPayload,
)
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.state.model.blockchain.block import Block
from bisq.core.dao.state.model.governance.dao_phase import DaoPhase
from bisq.core.network.p2p.persistence.append_only_data_store_listener import (
    AppendOnlyDataStoreListener,
)
from bisq.core.network.p2p.storage.hash_map_changed_listener import (
    HashMapChangedListener,
)
from bisq.core.network.p2p.storage.payload.persistable_network_payload import (
    PersistableNetworkPayload,
)
from bitcoinj.base.coin import Coin
from utils.data import ObservableList
from bisq.core.dao.governance.proposal.storage.appendonly.proposal_payload import (
    ProposalPayload,
)


if TYPE_CHECKING:
    from bisq.core.network.p2p.storage.payload.protected_storage_entry import (
        ProtectedStorageEntry,
    )
    from bisq.core.dao.governance.proposal.proposal_validator_provider import (
        ProposalValidatorProvider,
    )
    from bisq.core.dao.governance.proposal.storage.appendonly.proposal_storage_service import (
        ProposalStorageService,
    )
    from bisq.core.dao.governance.proposal.storage.temp.temp_proposal_storage_service import (
        TempProposalStorageService,
    )

    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.model.governance.proposal import Proposal
    from bisq.core.network.p2p.p2p_service import P2PService

    from bisq.core.network.p2p.persistence.append_only_data_store_service import (
        AppendOnlyDataStoreService,
    )
    from bisq.core.network.p2p.persistence.protected_data_store_service import (
        ProtectedDataStoreService,
    )
    from bisq.core.dao.governance.period.period_service import PeriodService


class ProposalService(
    HashMapChangedListener,
    AppendOnlyDataStoreListener,
    DaoStateListener,
    DaoSetupService,
):
    """
    Maintains protectedStoreList and appendOnlyStoreList for received proposals.
    Republishes protectedStoreList to append-only data store when entering the break before the blind vote phase.
    """

    def __init__(
        self,
        p2p_service: "P2PService",
        period_service: "PeriodService",
        proposal_storage_service: "ProposalStorageService",
        temp_proposal_storage_service: "TempProposalStorageService",
        append_only_data_store_service: "AppendOnlyDataStoreService",
        protected_data_store_service: "ProtectedDataStoreService",
        dao_state_service: "DaoStateService",
        validator_provider: "ProposalValidatorProvider",
    ):
        self.logger = get_ctx_logger(__name__)
        self.p2p_service = p2p_service
        self.period_service = period_service
        self.proposal_storage_service = proposal_storage_service
        self.temp_proposal_storage_service = temp_proposal_storage_service
        self.dao_state_service = dao_state_service
        self.validator_provider = validator_provider
        self.append_only_data_store_service = append_only_data_store_service
        self.protected_data_store_service = protected_data_store_service

        # fields

        # Proposals we receive in the proposal phase. They can be removed in that phase. That list must not be used for
        # consensus critical code.
        self.temp_proposals = ObservableList["Proposal"]()

        # Proposals which got added to the append-only data store in the break before the blind vote phase.
        # They cannot be removed anymore. This list is used for consensus critical code. Different nodes might have
        # different data collections due the eventually consistency of the P2P network.
        self.proposal_payloads = ObservableList["ProposalPayload"]()

        # We add our stores to the global stores
        self.append_only_data_store_service.add_service(proposal_storage_service)
        self.protected_data_store_service.add_service(temp_proposal_storage_service)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        self.dao_state_service.add_dao_state_listener(self)
        # Listen for tempProposals
        self.p2p_service.add_hash_set_changed_listener(self)
        # Listen for proposalPayloads
        self.p2p_service.p2p_data_storage.add_append_only_data_store_listener(self)

    def start(self):
        self._fill_list_from_protected_store()
        self._fill_list_from_append_only_data_store()

    def shut_down(self):
        self.dao_state_service.remove_dao_state_listener(self)
        self.p2p_service.remove_hash_map_changed_listener(self)
        self.p2p_service.p2p_data_storage.remove_append_only_data_store_listener(self)
        self.append_only_data_store_service.remove_service(self.proposal_storage_service)
        self.protected_data_store_service.remove_service(self.temp_proposal_storage_service)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // HashMapChangedListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_added(self, protected_storage_entries: Collection["ProtectedStorageEntry"]):
        for protected_storage_entry in protected_storage_entries:
            self._on_protected_data_added(protected_storage_entry, True)

    def on_removed(
        self, protected_storage_entries: Collection["ProtectedStorageEntry"]
    ):
        self._on_protected_data_removed(protected_storage_entries)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // AppendOnlyDataStoreListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_added(self, payload: "PersistableNetworkPayload"):
        self._on_append_only_data_added(payload, True)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_parse_block_complete_after_batch_processing(self, block: "Block"):
        # We try to broadcast at any block in the break1 phase. If we have received the data already we do not
        # broadcast so we do not flood the network.
        if self.period_service.is_in_phase(block.height, DaoPhase.Phase.BREAK1):
            # We only republish if we are completed with parsing old blocks, otherwise we would republish old
            # proposals all the time
            self._maybe_publish_to_append_only_data_store()
            self._fill_list_from_append_only_data_store()

    def on_parse_block_chain_complete(self):
        # Fill the lists with the data we have collected in our stores.
        self._fill_list_from_protected_store()
        self._fill_list_from_append_only_data_store()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_validated_proposals(self) -> list["Proposal"]:
        return [
            payload.proposal
            for payload in self.proposal_payloads
            if self.validator_provider.get_validator(payload.proposal).is_tx_type_valid(
                payload.proposal
            )
        ]

    def get_required_quorum(self, proposal: "Proposal") -> "Coin":
        tx = self.dao_state_service.get_tx(proposal.tx_id)
        chain_height = tx.block_height if tx else self.dao_state_service.chain_height
        return self.dao_state_service.get_param_value_as_coin(
            proposal.get_quorum_param(), chain_height
        )

    def get_required_threshold(self, proposal: "Proposal") -> float:
        tx = self.dao_state_service.get_tx(proposal.tx_id)
        chain_height = tx.block_height if tx else self.dao_state_service.chain_height
        return self.dao_state_service.get_param_value_as_percent_double(
            proposal.get_threshold_param(), chain_height
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _fill_list_from_protected_store(self):
        for entry in self.p2p_service.data_map.values():
            self._on_protected_data_added(entry, False)

    def _fill_list_from_append_only_data_store(self):
        for entry in self.proposal_storage_service.get_map().values():
            self._on_append_only_data_added(entry, False)

    def _maybe_publish_to_append_only_data_store(self):
        # We set reBroadcast to false to avoid to flood the network.
        # If we have 20 proposals and 200 nodes with 10 neighbor peers we would send 40 000 messages if we would set
        # reBroadcast to !
        for proposal in self.temp_proposals:
            if self.validator_provider.get_validator(proposal).is_valid_and_confirmed(
                proposal
            ):
                proposal_payload = ProposalPayload(proposal)
                success = self.p2p_service.add_persistable_network_payload(
                    proposal_payload, False
                )
                if success:
                    self.logger.info(
                        f"We published a ProposalPayload to the P2P network as append-only data. proposalTxId={proposal_payload.proposal.tx_id}"
                    )
                # If we had data already we did not broadcast and success is false

    def _on_protected_data_added(
        self, entry: "ProtectedStorageEntry", from_broadcast_message: bool
    ):
        protected_storage_payload = entry.protected_storage_payload
        if isinstance(protected_storage_payload, TempProposalPayload):
            proposal = protected_storage_payload.proposal
            # We do not validate if we are in current cycle and if tx is confirmed yet as the tx might be not
            # available/confirmed.
            # We check if we are in the proposal or break1 phase. We are tolerant to accept tempProposals in the break1
            # phase to avoid risks that a proposal published very closely to the end of the proposal phase will not be
            # sufficiently broadcast.
            # When we receive tempProposals from the seed node at startup we only keep those which are in the current
            # proposal/break1 phase if we are in that phase. We ignore tempProposals in case we are not in the
            # proposal/break1 phase as they are not used anyway but the proposalPayloads will be relevant once we
            # left the proposal/break1 phase.
            if self.period_service.is_in_phase(
                self.dao_state_service.chain_height, DaoPhase.Phase.PROPOSAL
            ) or self.period_service.is_in_phase(
                self.dao_state_service.chain_height, DaoPhase.Phase.BREAK1
            ):
                if proposal not in self.temp_proposals:
                    # We only validate in case the blocks are parsed as otherwise some validators like param validator
                    # might fail as Dao state is not complete.
                    if (
                        not self.dao_state_service.parse_block_chain_complete
                        or self.validator_provider.get_validator(
                            proposal
                        ).are_data_fields_valid(proposal)
                    ):
                        if from_broadcast_message:
                            self.logger.info(
                                f"We received a TempProposalPayload and store it to our protectedStoreList. proposalTxId={proposal.tx_id}"
                            )
                        self.temp_proposals.append(proposal)
                    else:
                        self.logger.debug(
                            f"We received an invalid proposal from the P2P network. Proposal={proposal}, blockHeight={self.dao_state_service.chain_height}"
                        )

    def _on_protected_data_removed(
        self, protected_storage_entries: Collection["ProtectedStorageEntry"]
    ):
        # The listeners of tmpProposals can do large amounts of work that cause performance issues. Apply all of the
        # updates at once using retainAll which will cause all listeners to be updated only once.
        temp_proposals_with_updates = list(self.temp_proposals)

        for protected_storage_entry in protected_storage_entries:
            protected_storage_payload = (
                protected_storage_entry.protected_storage_payload
            )
            if isinstance(protected_storage_payload, TempProposalPayload):
                proposal = protected_storage_payload.proposal
                # We allow removal only if we are in the proposal phase.
                in_phase = self.period_service.is_in_phase(
                    self.dao_state_service.chain_height, DaoPhase.Phase.PROPOSAL
                )
                tx_in_past_cycle = self.period_service.is_tx_in_past_cycle(
                    proposal.tx_id, self.dao_state_service.chain_height
                )
                tx = self.dao_state_service.get_tx(proposal.tx_id)
                unconfirmed_or_non_bsq_tx = tx is None
                # if the tx is unconfirmed we need to be in the PROPOSAL phase, otherwise the tx must be confirmed
                if in_phase or tx_in_past_cycle or unconfirmed_or_non_bsq_tx:
                    try:
                        temp_proposals_with_updates.remove(proposal)
                        self.logger.debug(
                            f"We received a remove request for a TempProposalPayload and have removed the proposal "
                            f"from our list. proposal creation date={proposal.get_creation_date_as_date()}, proposalTxId={proposal.tx_id}, inPhase={in_phase}, "
                            f"txInPastCycle={tx_in_past_cycle}, unconfirmedOrNonBsqTx={unconfirmed_or_non_bsq_tx}"
                        )
                    except:
                        pass
                else:
                    self.logger.warning(
                        f"We received a remove request outside the PROPOSAL phase. "
                        f"Proposal creation date={proposal.get_creation_date_as_date()}, proposal.txId={proposal.tx_id}, current blockHeight={self.dao_state_service.chain_height}"
                    )

        self.temp_proposals.retain_all(temp_proposals_with_updates)

    def _on_append_only_data_added(
        self,
        persistable_network_payload: "PersistableNetworkPayload",
        from_broadcast_message: bool,
    ):
        if isinstance(persistable_network_payload, ProposalPayload):
            proposal_payload = persistable_network_payload
            if proposal_payload not in self.proposal_payloads:
                proposal = proposal_payload.proposal

                # We don't validate phase and cycle as we might receive proposals from other cycles or phases at startup.
                # Beside that we might receive payloads we requested at the vote result phase in case we missed some
                # payloads. We prefer here resilience over protection against late publishing attacks.

                # We only validate in case the blocks are parsed as otherwise some validators like param validator
                # might fail as Dao state is not complete.
                if (
                    not self.dao_state_service.parse_block_chain_complete
                    or self.validator_provider.get_validator(
                        proposal
                    ).are_data_fields_valid(proposal)
                ):
                    if from_broadcast_message:
                        self.logger.info(
                            f"We received a ProposalPayload and store it to our appendOnlyStoreList. proposalTxId={proposal.tx_id}"
                        )
                    self.proposal_payloads.append(proposal_payload)
                else:
                    self.logger.warning(
                        f"We received an invalid append-only proposal from the P2P network. Proposal={proposal}, blockHeight={self.dao_state_service.chain_height}"
                    )
