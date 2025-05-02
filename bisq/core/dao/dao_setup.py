from collections.abc import Callable
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from bisq.core.dao.governance.proposal.proposal_list_presentation import (
        ProposalListPresentation,
    )
    from bisq.core.dao.burningman.accounting.node.accounting_node_provider import (
        AccountingNodeProvider,
    )
    from bisq.core.dao.node.bsq_node_provider import BsqNodeProvider
    from bisq.core.dao.governance.votereveal.vote_reveal_service import (
        VoteRevealService,
    )
    from bisq.core.dao.monitoring.blind_vote_state_monitoring_service import (
        BlindVoteStateMonitoringService,
    )
    from bisq.core.dao.monitoring.proposal_state_monitoring_service import (
        ProposalStateMonitoringService,
    )
    from bisq.core.dao.dao_kill_switch import DaoKillSwitch
    from bisq.core.dao.governance.asset.asset_service import AssetService
    from bisq.core.dao.governance.proofofburn.proof_of_burn_service import (
        ProofOfBurnService,
    )
    from bisq.core.dao.burningman.accounting.node.accounting_node import AccountingNode
    from bisq.core.dao.burningman.burning_man_accounting_service import (
        BurningManAccountingService,
    )
    from bisq.core.dao.dao_facade import DaoFacade
    from bisq.core.dao.dao_setup_service import DaoSetupService
    from bisq.core.dao.governance.ballot.ballot_list_service import BallotListService
    from bisq.core.dao.governance.blindvote.blind_vote_list_service import (
        BlindVoteListService,
    )
    from bisq.core.dao.governance.blindvote.my_blind_vote_list_service import (
        MyBlindVoteListService,
    )
    from bisq.core.dao.governance.bond.reputation.bonded_reputation_repository import (
        BondedReputationRepository,
    )
    from bisq.core.dao.governance.bond.reputation.my_bonded_reputation_repository import (
        MyBondedReputationRepository,
    )
    from bisq.core.dao.governance.bond.reputation.my_reputation_list_service import (
        MyReputationListService,
    )
    from bisq.core.dao.governance.bond.role.bonded_roles_repository import (
        BondedRolesRepository,
    )
    from bisq.core.dao.governance.period.cycle_service import CycleService
    from bisq.core.dao.governance.proposal.proposal_service import ProposalService
    from bisq.core.dao.governance.voteresult.missing_data_request_service import (
        MissingDataRequestService,
    )
    from bisq.core.dao.governance.voteresult.vote_result_service import (
        VoteResultService,
    )
    from bisq.core.dao.monitoring.dao_state_monitoring_service import (
        DaoStateMonitoringService,
    )
    from bisq.core.dao.node.bsq_node import BsqNode
    from bisq.core.dao.node.explorer.export_json_file_manager import (
        ExportJsonFilesService,
    )
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.dao_state_snapshot_service import DaoStateSnapshotService


class DaoSetup:
    """
    High level entry point for Dao domain.
    We initialize all main service classes here to be sure they are started.
    """

    def __init__(
        self,
        bsq_node_provider: "BsqNodeProvider",
        accounting_node_provider: "AccountingNodeProvider",
        dao_state_service: "DaoStateService",
        cycle_service: "CycleService",
        ballot_list_service: "BallotListService",
        proposal_service: "ProposalService",
        proposal_list_presentation: "ProposalListPresentation",
        blind_vote_list_service: "BlindVoteListService",
        my_blind_vote_list_service: "MyBlindVoteListService",
        vote_reveal_service: "VoteRevealService",
        vote_result_service: "VoteResultService",
        missing_data_request_service: "MissingDataRequestService",
        bonded_reputation_repository: "BondedReputationRepository",
        bonded_roles_repository: "BondedRolesRepository",
        my_reputation_list_service: "MyReputationListService",
        my_bonded_reputation_repository: "MyBondedReputationRepository",
        asset_service: "AssetService",
        proof_of_burn_service: "ProofOfBurnService",
        dao_facade: "DaoFacade",
        export_json_files_service: "ExportJsonFilesService",
        dao_kill_switch: "DaoKillSwitch",
        dao_state_monitoring_service: "DaoStateMonitoringService",
        proposal_state_monitoring_service: "ProposalStateMonitoringService",
        blind_vote_state_monitoring_service: "BlindVoteStateMonitoringService",
        dao_state_snapshot_service: "DaoStateSnapshotService",
        burning_man_accounting_service: "BurningManAccountingService",
    ):
        self._bsq_node = bsq_node_provider.bsq_node
        self._accounting_node = accounting_node_provider.accounting_node

        # order of the list matters (?)
        self._dao_setup_services: list["DaoSetupService"] = [
            dao_state_service,
            cycle_service,
            ballot_list_service,
            proposal_service,
            proposal_list_presentation,
            blind_vote_list_service,
            my_blind_vote_list_service,
            vote_reveal_service,
            vote_result_service,
            missing_data_request_service,
            bonded_reputation_repository,
            bonded_roles_repository,
            my_reputation_list_service,
            my_bonded_reputation_repository,
            asset_service,
            proof_of_burn_service,
            dao_facade,
            export_json_files_service,
            dao_kill_switch,
            dao_state_monitoring_service,
            proposal_state_monitoring_service,
            blind_vote_state_monitoring_service,
            dao_state_snapshot_service,
            burning_man_accounting_service,
            #
            self._bsq_node,
            self._accounting_node,
        ]

    def on_all_services_initialized(
        self,
        error_message_handler: Callable[[str], None],
        warn_message_handler: Callable[[str], None],
    ):
        self._bsq_node.error_message_handler = error_message_handler
        self._bsq_node.warn_message_handler = warn_message_handler

        self._accounting_node.error_message_handler = error_message_handler
        self._accounting_node.warn_message_handler = warn_message_handler

        # We add first all listeners at all services and then call the start methods.
        # Some services are listening on others so we need to make sure that the
        # listeners are set before we call start as that might trigger state change
        # which triggers listeners.
        for service in self._dao_setup_services:
            service.add_listeners()
        for service in self._dao_setup_services:
            service.start()

    def shut_down(self):
        self._bsq_node.shut_down()
        self._accounting_node.shut_down()
        for service in self._dao_setup_services:
            if getattr(service, "shut_down", None):
                service.shut_down()
