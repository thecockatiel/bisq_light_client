from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from bisq.common.handlers.error_message_handler import ErrorMessageHandler
from bisq.common.handlers.result_handler import ResultHandler
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.governance.blindvote.blind_vote_consensus import BlindVoteConsensus
from bisq.core.dao.governance.bond.lockup.lockup_reason import LockupReason
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.governance.proposal.compensation.compensation_consensus import (
    CompensationConsensus,
)
from bisq.core.dao.governance.proposal.proposal_consensus import ProposalConsensus
from bisq.core.dao.governance.proposal.reimbursement.reimbursement_consensus import (
    ReimbursementConsensus,
)
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bisq.core.dao.state.model.governance.bonded_role_type import BondedRoleType
from bisq.core.dao.governance.proposal.issuance_proposal import IssuanceProposal
from bisq.core.dao.state.model.governance.dao_phase import DaoPhase
from bisq.core.dao.state.model.governance.issuance_type import IssuanceType
from bisq.core.trade.delayed_payout_address_provider import DelayedPayoutAddressProvider
from bitcoinj.base.coin import Coin
from utils.data import SimpleProperty
from utils.preconditions import check_argument


if TYPE_CHECKING:
    from bisq.core.dao.state.model.governance.cycle import Cycle
    from bisq.core.dao.state.model.governance.role_proposal import RoleProposal
    from bisq.core.dao.state.model.blockchain.tx_output_key import TxOutputKey
    from bisq.asset.asset import Asset
    from bisq.core.dao.state.model.governance.role import Role
    from bisq.core.dao.state.model.governance.vote import Vote
    from bisq.core.dao.state.model.governance.ballot import Ballot
    from bisq.core.dao.governance.myvote.my_vote_list_service import MyVoteListService
    from bitcoinj.core.transaction import Transaction
    from bisq.core.dao.state.model.governance.proposal import Proposal
    from bisq.core.dao.governance.bond.unlock.unlock_tx_service import UnlockTxService
    from bisq.core.dao.governance.bond.lockup.lockup_tx_service import LockupTxService
    from bisq.core.dao.governance.ballot.ballot_list_presentation import (
        BallotListPresentation,
    )
    from bisq.core.dao.governance.bond.reputation.bonded_reputation_repository import (
        BondedReputationRepository,
    )
    from bisq.core.dao.governance.bond.reputation.my_bonded_reputation_repository import (
        MyBondedReputationRepository,
    )
    from bisq.core.dao.governance.bond.role.bonded_roles_repository import (
        BondedRolesRepository,
    )
    from bisq.core.dao.governance.proposal.compensation.compensation_proposal_factory import (
        CompensationProposalFactory,
    )
    from bisq.core.dao.governance.proposal.confiscatebond.confiscate_bond_proposal_factory import (
        ConfiscateBondProposalFactory,
    )
    from bisq.core.dao.governance.proposal.generic.generic_proposal_factory import (
        GenericProposalFactory,
    )
    from bisq.core.dao.governance.proposal.param.change_param_proposal_factory import (
        ChangeParamProposalFactory,
    )
    from bisq.core.dao.governance.proposal.reimbursement.reimbursement_proposal_factory import (
        ReimbursementProposalFactory,
    )
    from bisq.core.dao.governance.proposal.remove_asset.remove_asset_proposal_factory import (
        RemoveAssetProposalFactory,
    )
    from bisq.core.dao.governance.proposal.role.role_proposal_factory import (
        RoleProposalFactory,
    )
    from bisq.core.dao.governance.blindvote.my_blind_vote_list_service import (
        MyBlindVoteListService,
    )
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.governance.period.cycle_service import CycleService
    from bisq.core.dao.state.storage.dao_state_storage_service import (
        DaoStateStorageService,
    )
    from bisq.core.dao.monitoring.dao_state_monitoring_service import (
        DaoStateMonitoringService,
    )
    from bisq.core.dao.governance.ballot.ballot_list_service import BallotListService
    from bisq.core.dao.governance.proposal.proposal_service import ProposalService
    from bisq.core.dao.governance.proposal.proposal_list_presentation import (
        ProposalListPresentation,
    )
    from bisq.core.dao.governance.proposal.my_proposal_list_service import (
        MyProposalListService,
    )
    from bisq.common.config.config import Config
    from bisq.core.dao.state.dao_state_service import DaoStateService


class DaoFacade(DaoSetupService):
    """
    Provides a facade to interact with the Dao domain. Hides complexity and domain details to clients (e.g. UI or APIs)
    by providing a reduced API and/or aggregating subroutines.
    """

    def __init__(
        self,
        my_proposal_list_service: "MyProposalListService",
        proposal_list_presentation: "ProposalListPresentation",
        proposal_service: "ProposalService",
        ballot_list_service: "BallotListService",
        ballot_list_presentation: "BallotListPresentation",
        dao_state_service: "DaoStateService",
        dao_state_monitoring_service: "DaoStateMonitoringService",
        period_service: "PeriodService",
        cycle_service: "CycleService",
        my_blind_vote_list_service: "MyBlindVoteListService",
        my_vote_list_service: "MyVoteListService",
        compensation_proposal_factory: "CompensationProposalFactory",
        reimbursement_proposal_factory: "ReimbursementProposalFactory",
        change_param_proposal_factory: "ChangeParamProposalFactory",
        confiscate_bond_proposal_factory: "ConfiscateBondProposalFactory",
        role_proposal_factory: "RoleProposalFactory",
        generic_proposal_factory: "GenericProposalFactory",
        remove_asset_proposal_factory: "RemoveAssetProposalFactory",
        bonded_roles_repository: "BondedRolesRepository",
        bonded_reputation_repository: "BondedReputationRepository",
        my_bonded_reputation_repository: "MyBondedReputationRepository",
        lockup_tx_service: "LockupTxService",
        unlock_tx_service: "UnlockTxService",
        dao_state_storage_service: "DaoStateStorageService",
        config: "Config",
    ):
        self._proposal_list_presentation = proposal_list_presentation
        self._proposal_service = proposal_service
        self._ballot_list_service = ballot_list_service
        self._ballot_list_presentation = ballot_list_presentation
        self._my_proposal_list_service = my_proposal_list_service
        self._dao_state_service = dao_state_service
        self._dao_state_monitoring_service = dao_state_monitoring_service
        self._period_service = period_service
        self._cycle_service = cycle_service
        self._my_blind_vote_list_service = my_blind_vote_list_service
        self._my_vote_list_service = my_vote_list_service
        self._compensation_proposal_factory = compensation_proposal_factory
        self._reimbursement_proposal_factory = reimbursement_proposal_factory
        self._change_param_proposal_factory = change_param_proposal_factory
        self._confiscate_bond_proposal_factory = confiscate_bond_proposal_factory
        self._role_proposal_factory = role_proposal_factory
        self._generic_proposal_factory = generic_proposal_factory
        self._remove_asset_proposal_factory = remove_asset_proposal_factory
        self._bonded_roles_repository = bonded_roles_repository
        self._bonded_reputation_repository = bonded_reputation_repository
        self._my_bonded_reputation_repository = my_bonded_reputation_repository
        self._lockup_tx_service = lockup_tx_service
        self._unlock_tx_service = unlock_tx_service
        self._dao_state_storage_service = dao_state_storage_service
        self._config = config

        self.phase_property = SimpleProperty(DaoPhase.Phase.UNDEFINED)
        self._subscriptions: list[Callable[[], None]] = []

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        class Listener(DaoStateListener):
            def on_new_block_height(self_, block_height: int):
                if block_height > 0 and self._period_service.current_cycle is not None:
                    phase = self._period_service.current_cycle.get_phase_for_height(
                        block_height
                    )
                    if phase is not None:
                        self.phase_property.set(phase)

        self._subscriptions.append(
            self._dao_state_service.add_dao_state_listener(Listener())
        )

    def start(self):
        pass

    def add_bsq_state_listener(self, listener: DaoStateListener):
        return self._dao_state_service.add_dao_state_listener(listener)

    def remove_bsq_state_listener(self, listener: DaoStateListener):
        self._dao_state_service.remove_dao_state_listener(listener)

    def shut_down(self):
        for unsub in self._subscriptions:
            unsub()
        self._subscriptions.clear()
        self._my_proposal_list_service.shut_down()
        self._ballot_list_presentation.shut_down()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # //
    # // Phase: Proposal
    # //
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Use case: Present lists
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_active_or_my_unconfirmed_proposals(self):
        return self._proposal_list_presentation.active_or_my_unconfirmed_proposals

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Use case: Create proposal
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_compensation_proposal_with_transaction(
        self,
        name: str,
        link: str,
        requested_bsq: Coin,
        burning_man_receiver_address: str = None,
    ):
        return self._compensation_proposal_factory.create_proposal_with_transaction(
            name, link, requested_bsq, burning_man_receiver_address
        )

    def get_reimbursement_proposal_with_transaction(
        self, name: str, link: str, requested_bsq: Coin
    ):
        return self._reimbursement_proposal_factory.create_proposal_with_transaction(
            name, link, requested_bsq
        )

    def get_param_proposal_with_transaction(
        self, name: str, link: str, param: Param, param_value: str
    ):
        return self._change_param_proposal_factory.create_proposal_with_transaction(
            name, link, param, param_value
        )

    def get_confiscate_bond_proposal_with_transaction(
        self, name: str, link: str, lockup_tx_id: str
    ):
        return self._confiscate_bond_proposal_factory.create_proposal_with_transaction(
            name, link, lockup_tx_id
        )

    def get_bonded_role_proposal_with_transaction(self, role: "Role"):
        return self._role_proposal_factory.create_proposal_with_transaction(role)

    def get_generic_proposal_with_transaction(self, name: str, link: str):
        return self._generic_proposal_factory.create_proposal_with_transaction(
            name, link
        )

    def get_remove_asset_proposal_with_transaction(
        self, name: str, link: str, asset: "Asset"
    ):
        return self._remove_asset_proposal_factory.create_proposal_with_transaction(
            name, link, asset
        )

    def get_bonded_roles(self):
        return self._bonded_roles_repository.bonds

    def get_accepted_bonded_roles(self):
        return self._bonded_roles_repository.get_accepted_bonds()

    def get_proposal_fee(self, chain_height: int):
        return ProposalConsensus.get_fee(self._dao_state_service, chain_height)

    # Publish proposal tx, proposal payload and persist it to myProposalList
    def publish_my_proposal(
        self,
        proposal: "Proposal",
        transaction: "Transaction",
        result_handler: "ResultHandler",
        error_message_handler: "ErrorMessageHandler",
    ):
        self._my_proposal_list_service.publish_tx_and_payload(
            proposal, transaction, result_handler, error_message_handler
        )

    def is_my_proposal(self, proposal: "Proposal"):
        return self._my_proposal_list_service.is_mine(proposal)

    def remove_my_proposal(self, proposal: "Proposal"):
        return self._my_proposal_list_service.remove(proposal)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # //
    # // Phase: Blind Vote
    # //
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Use case: Present lists
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_all_ballots(self):
        return self._ballot_list_presentation.all_ballots

    def get_all_valid_ballots(self):
        return self._ballot_list_presentation.get_all_valid_ballots()

    def get_ballots_of_cycle(self):
        return self._ballot_list_presentation.ballots_of_cycle

    def get_merit_and_stake_for_proposal(self, proposal_tx_id: str):
        return self._my_vote_list_service.get_merit_and_stake_for_proposal(
            proposal_tx_id,
            self._my_blind_vote_list_service,
        )

    def get_available_merit(self):
        return self._my_blind_vote_list_service.get_currently_available_merit()

    def get_my_vote_list_for_cycle(self):
        return self._my_vote_list_service.get_my_vote_list_for_cycle()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Use case: Vote
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def set_vote(self, ballot: "Ballot", vote: "Vote" = None):
        self._ballot_list_service.set_vote(ballot, vote)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Use case: Create blindVote
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # When creating blind vote we present fee
    def get_blind_vote_fee_for_cycle(self) -> Coin:
        return BlindVoteConsensus.get_fee(
            self._dao_state_service, self._dao_state_service.chain_height
        )

    def get_blind_vote_mining_fee_and_tx_vsize(self, stake: Coin):
        return self._my_blind_vote_list_service.get_mining_fee_and_tx_vsize(stake)

    # Publish blindVote tx and broadcast blindVote to p2p network and store to blindVoteList.
    def publish_blind_vote(
        self,
        stake: Coin,
        result_handler: Callable[[], None],
        exception_handler: Callable[[Exception], None],
    ):
        self._my_blind_vote_list_service.publish_blind_vote(
            stake,
            result_handler,
            exception_handler,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # //
    # // Generic
    # //
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Use case: Presentation of phases
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # Because last block in request and voting phases must not be used for making a tx as it will get confirmed in the
    # next block which would be already the next phase we hide that last block to the user and add it to the break.
    def get_first_block_of_phase_for_display(
        self, height: int, phase: DaoPhase.Phase
    ) -> int:
        first_block = self._period_service.get_first_block_of_phase(height, phase)
        if phase == DaoPhase.Phase.UNDEFINED:
            pass
        elif phase == DaoPhase.Phase.PROPOSAL:
            pass
        elif phase == DaoPhase.Phase.BREAK1:
            first_block -= 1
        elif phase == DaoPhase.Phase.BLIND_VOTE:
            pass
        elif phase == DaoPhase.Phase.BREAK2:
            first_block -= 1
        elif phase == DaoPhase.Phase.VOTE_REVEAL:
            pass
        elif phase == DaoPhase.Phase.BREAK3:
            first_block -= 1
        elif phase == DaoPhase.Phase.RESULT:
            pass
        return first_block

    def get_block_start_date_by_cycle_index(self) -> dict[int, datetime]:
        return {
            self._cycle_service.get_cycle_index(cycle): datetime.fromtimestamp(
                self._dao_state_service.get_block_time(cycle.height_of_first_block)
                / 1000
            )
            for cycle in self._period_service.cycles
        }

    # Because last block in request and voting phases must not be used for making a tx as it will get confirmed in the
    # next block which would be already the next phase we hide that last block to the user and add it to the break.
    def get_last_block_of_phase_for_display(
        self, height: int, phase: DaoPhase.Phase
    ) -> int:
        last_block = self._period_service.get_last_block_of_phase(height, phase)
        if phase == DaoPhase.Phase.UNDEFINED:
            pass
        elif phase == DaoPhase.Phase.PROPOSAL:
            last_block -= 1
        elif phase == DaoPhase.Phase.BREAK1:
            pass
        elif phase == DaoPhase.Phase.BLIND_VOTE:
            last_block -= 1
        elif phase == DaoPhase.Phase.BREAK2:
            pass
        elif phase == DaoPhase.Phase.VOTE_REVEAL:
            last_block -= 1
        elif phase == DaoPhase.Phase.BREAK3:
            pass
        elif phase == DaoPhase.Phase.RESULT:
            pass
        return last_block

    # Because last block in request and voting phases must not be used for making a tx as it will get confirmed in the
    # next block which would be already the next phase we hide that last block to the user and add it to the break.
    def get_duration_for_phase_for_display(self, phase: DaoPhase.Phase) -> int:
        duration = self._period_service.get_duration_for_phase(
            phase, self._dao_state_service.chain_height
        )
        if phase == DaoPhase.Phase.UNDEFINED:
            pass
        elif phase == DaoPhase.Phase.PROPOSAL:
            duration -= 1
        elif phase == DaoPhase.Phase.BREAK1:
            duration += 1
        elif phase == DaoPhase.Phase.BLIND_VOTE:
            duration -= 1
        elif phase == DaoPhase.Phase.BREAK2:
            duration += 1
        elif phase == DaoPhase.Phase.VOTE_REVEAL:
            duration -= 1
        elif phase == DaoPhase.Phase.BREAK3:
            duration += 1
        elif phase == DaoPhase.Phase.RESULT:
            pass
        return duration

    @property
    def current_cycle_duration(self) -> int:
        current_cycle = self._period_service.current_cycle
        return current_cycle.get_duration() if current_cycle is not None else 0

    @property
    def chain_height(self):
        return self._dao_state_service.chain_height

    @property
    def block_at_chain_height(self):
        return self.get_block_at_height(self.chain_height)

    def get_block_at_height(self, chain_height: int):
        return self._dao_state_service.get_block_at_height(chain_height)

    @property
    def is_dao_state_ready_and_in_sync(self) -> bool:
        return (
            self._dao_state_service.parse_block_chain_complete
            and not self._dao_state_monitoring_service.is_in_conflict_with_seed_node
            and not self._dao_state_monitoring_service.dao_state_block_chain_not_connecting
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Use case: Bonding
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def publish_lockup_tx(
        self,
        lockup_amount: Coin,
        lock_time: int,
        lockup_reason: LockupReason,
        hash: bytes,
        result_handler: Callable[[str], None],
        exception_handler: Callable[[Exception], None],
    ):
        self._lockup_tx_service.publish_lockup_tx(
            lockup_amount,
            lock_time,
            lockup_reason,
            hash,
            result_handler,
            exception_handler,
        )

    def get_lockup_tx_mining_fee_and_tx_vsize(
        self,
        lockup_amount: Coin,
        lock_time: int,
        lockup_reason: LockupReason,
        hash: bytes,
    ) -> tuple[Coin, int]:
        return self._lockup_tx_service.get_mining_fee_and_tx_vsize(
            lockup_amount,
            lock_time,
            lockup_reason,
            hash,
        )

    def publish_unlock_tx(
        self,
        lockup_tx_id: str,
        result_handler: Callable[[str], None],
        exception_handler: Callable[[Exception], None],
    ):
        self._unlock_tx_service.publish_unlock_tx(
            lockup_tx_id,
            result_handler,
            exception_handler,
        )

    def get_unlock_tx_mining_fee_and_tx_vsize(
        self, lockup_tx_id: str
    ) -> tuple[Coin, int]:
        return self._unlock_tx_service.get_mining_fee_and_tx_vsize(lockup_tx_id)

    def get_total_lockup_amount(self) -> int:
        return self._dao_state_service.get_total_lockup_amount()

    def get_total_amount_of_unlocking_tx_outputs(self) -> int:
        return self._dao_state_service.get_total_amount_of_unlocking_tx_outputs()

    def get_total_amount_of_unlocked_tx_outputs(self) -> int:
        return self._dao_state_service.get_total_amount_of_unlocked_tx_outputs()

    def get_total_amount_of_confiscated_tx_outputs(self) -> int:
        return self._dao_state_service.get_total_amount_of_confiscated_tx_outputs()

    # Contains burned fee and invalidated bsq due invalid txs
    def get_total_amount_of_burnt_bsq(self) -> int:
        return self._dao_state_service.get_total_amount_of_burnt_bsq()

    def get_invalid_txs(self):
        return self._dao_state_service.get_invalid_txs()

    def get_irregular_txs(self):
        return self._dao_state_service.get_irregular_txs()

    def get_lock_time(self, tx_id: str):
        return self._dao_state_service.get_lock_time(tx_id)

    def get_all_bonds(self):
        bonds = list(self._bonded_reputation_repository.bonds)
        bonds.extend(self._bonded_roles_repository.bonds)
        return bonds

    def get_all_active_bonds(self):
        bonds = list(self._bonded_reputation_repository.get_active_bonds())
        bonds.extend(self._bonded_roles_repository.get_active_bonds())
        return bonds

    def get_my_bonded_reputations(self):
        return self._my_bonded_reputation_repository.my_bonded_reputations

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Use case: Present transaction related state
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_tx(self, tx_id: str):
        return self._dao_state_service.get_tx(tx_id)

    @property
    def genesis_block_height(self) -> int:
        return self._dao_state_service.genesis_block_height

    @property
    def genesis_tx_id(self) -> str:
        return self._dao_state_service.genesis_tx_id

    @property
    def genesis_total_supply(self) -> Coin:
        return self._dao_state_service.genesis_total_supply

    def get_num_issuance_transactions(self, issuance_type: IssuanceType) -> int:
        return len(self._dao_state_service.get_issuance_set_for_type(issuance_type))

    def get_burnt_fee_txs(self):
        return self._dao_state_service.get_burnt_fee_txs()

    def get_unspent_tx_outputs(self):
        return self._dao_state_service.get_unspent_tx_outputs()

    def is_tx_output_spendable(self, tx_output_key: "TxOutputKey"):
        return self._dao_state_service.is_tx_output_key_spendable(tx_output_key)

    def get_unspent_tx_output_value(self, key: "TxOutputKey"):
        return self._dao_state_service.get_unspent_tx_output_value(key)

    def get_num_txs(self):
        return self._dao_state_service.get_num_txs()

    def get_lockup_tx_output(self, tx_id: str):
        return self._dao_state_service.get_lockup_tx_output(tx_id)

    def get_total_issued_amount(self, issuance_type: IssuanceType):
        return self._dao_state_service.get_total_issued_amount(issuance_type)

    def get_block_time(self, issuance_block_height: int):
        return self._dao_state_service.get_block_time(issuance_block_height)

    def get_issuance_block_height(self, tx_id: str):
        return self._dao_state_service.get_issuance_block_height(tx_id)

    def is_issuance_tx(self, tx_id: str, issuance_type: IssuanceType):
        return self._dao_state_service.is_issuance_tx(tx_id, issuance_type)

    def has_tx_burnt_fee(self, hash_as_string: str):
        return self._dao_state_service.has_tx_burnt_fee(hash_as_string)

    def get_optional_tx_type(self, tx_id: str):
        return self._dao_state_service.get_optional_tx_type(tx_id)

    def get_tx_type(self, tx_id: str):
        tx = self._dao_state_service.get_tx(tx_id)
        if tx and tx.tx_type:
            return tx.tx_type
        return TxType.UNDEFINED_TX_TYPE

    def is_in_phase_but_not_last_block(self, phase: DaoPhase.Phase):
        return self._period_service.is_in_phase_but_not_last_block(phase)

    def is_tx_in_correct_cycle(self, tx_height: int, chain_height: int):
        return self._period_service.is_tx_in_correct_cycle(tx_height, chain_height)

    def is_tx_in_correct_cycle_by_id(self, tx_id: str, chain_height: int):
        return self._period_service.is_tx_in_correct_cycle_by_id(tx_id, chain_height)

    def get_min_compensation_request_amount(self):
        return CompensationConsensus.get_min_compensation_request_amount(
            self._dao_state_service, self._period_service.chain_height
        )

    def get_max_compensation_request_amount(self):
        return CompensationConsensus.get_max_compensation_request_amount(
            self._dao_state_service, self._period_service.chain_height
        )

    def get_min_reimbursement_request_amount(self):
        return ReimbursementConsensus.get_min_reimbursement_request_amount(
            self._dao_state_service, self._period_service.chain_height
        )

    def get_max_reimbursement_request_amount(self):
        return ReimbursementConsensus.get_max_reimbursement_request_amount(
            self._dao_state_service, self._period_service.chain_height
        )

    def get_param_value(self, param: Param, block_height: int = None) -> str:
        if block_height is None:
            block_height = self._period_service.chain_height

        return self._dao_state_service.get_param_value(param, block_height)

    def resync_dao_state_from_genesis(self, result_handler: Callable[[], None]):
        self._dao_state_storage_service.resync_dao_state_from_genesis(result_handler)

    def remove_and_backup_all_dao_data(self, storage_dir: Path):
        self._dao_state_storage_service.remove_and_backup_all_dao_data(storage_dir)

    def is_my_role(self, role: "Role") -> bool:
        return self._bonded_roles_repository.is_my_role(role)

    def get_issuance_for_cycle(self, cycle: "Cycle") -> int:
        return sum(
            ep.proposal.get_requested_bsq().value
            for ep in self._dao_state_service.get_evaluated_proposal_list()
            if ep.is_accepted
            and self._cycle_service.is_tx_in_cycle(cycle, ep.proposal.tx_id)
            and isinstance(ep.proposal, IssuanceProposal)
        )

    def get_bond_by_lockup_tx_id(self, lockup_tx_id: str):
        return next(
            (
                bond
                for bond in self.get_all_bonds()
                if bond.lockup_tx_id == lockup_tx_id
            ),
            None,
        )

    def get_required_threshold(self, proposal: "Proposal") -> float:
        return self._proposal_service.get_required_threshold(proposal)

    def get_required_quorum(self, proposal: "Proposal") -> Coin:
        return self._proposal_service.get_required_quorum(proposal)

    def get_required_bond(self, role_proposal: Optional["RoleProposal"]) -> int:
        # TODO: check later
        if role_proposal:
            bonded_role_type = role_proposal.role.bonded_role_type
        else:
            bonded_role_type = None
        check_argument(bonded_role_type is not None, "bonded_role_type must be present")
        tx = self._dao_state_service.get_tx(role_proposal.tx_id)
        if tx:
            height = tx.block_height
        else:
            height = self._dao_state_service.chain_height
        required_bond_unit = (
            role_proposal.required_bond_unit or bonded_role_type.required_bond_unit
        )
        base_factor = self._dao_state_service.get_param_value_as_coin(
            Param.BONDED_ROLE_FACTOR, height
        ).value
        return required_bond_unit * base_factor

    def get_required_bond_of_type(self, bonded_role_type: "BondedRoleType") -> int:
        height = self._dao_state_service.chain_height
        required_bond_unit = bonded_role_type.required_bond_unit
        base_factor = self._dao_state_service.get_param_value_as_coin(
            Param.BONDED_ROLE_FACTOR, height
        ).value
        return required_bond_unit * base_factor

    def get_all_past_param_values(self, param: Param) -> set:
        _set = set[str]()
        for cycle in self._period_service.cycles:
            _set.add(self.get_param_value(param, cycle.height_of_first_block))
        return _set

    def get_all_donation_addresses(self):
        # We support any of the past addresses as well as in case the peer has not enabled the DAO or is out of sync we
        # do not want to break validation.
        all_past_param_values = self.get_all_past_param_values(
            Param.RECIPIENT_BTC_ADDRESS
        )

        # If Dao is deactivated we need to add the default address as getAllPastParamValues will not return us any.
        if not all_past_param_values:
            all_past_param_values.add(Param.RECIPIENT_BTC_ADDRESS.default_value)

        if self._config.base_currency_network.is_mainnet():
            # If Dao is deactivated we need to add the past addresses used as well.
            # This list need to be updated once a new address gets defined.
            all_past_param_values.add(DelayedPayoutAddressProvider.BM2019_ADDRESS)
            all_past_param_values.add(DelayedPayoutAddressProvider.BM2_ADDRESS)
            all_past_param_values.add(DelayedPayoutAddressProvider.BM3_ADDRESS)

        return all_past_param_values

    @property
    def is_parse_block_chain_complete(self):
        return self._dao_state_service.parse_block_chain_complete
