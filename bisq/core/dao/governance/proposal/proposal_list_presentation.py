from typing import TYPE_CHECKING, Iterable
from bisq.common.user_thread import UserThread
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.governance.proposal.my_proposal_list_service_listener import (
    MyProposalListServiceListener,
)
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bitcoinj.core.transaction_confidence_type import TransactionConfidenceType
from utils.data import FilteredList, ObservableList

if TYPE_CHECKING:
    from bisq.core.dao.state.model.blockchain.block import Block
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.dao.governance.proposal.my_proposal_list_service import (
        MyProposalListService,
    )
    from bisq.core.dao.governance.proposal.proposal_service import ProposalService
    from bisq.core.dao.governance.proposal.proposal_validator_provider import (
        ProposalValidatorProvider,
    )
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.model.governance.proposal import Proposal


class ProposalListPresentation(
    DaoStateListener, MyProposalListServiceListener, DaoSetupService
):
    """
    Provides filtered observableLists of the Proposals from proposalService and myProposalListService.
    We want to show the own proposals in unconfirmed state (validation of phase and cycle cannot be done but as it is
    our own proposal that is not critical). Foreign proposals are only shown if confirmed and fully validated.
    """

    def __init__(
        self,
        proposal_service: "ProposalService",
        dao_state_service: "DaoStateService",
        my_proposal_list_service: "MyProposalListService",
        bsq_wallet_service: "BsqWalletService",
        validator_provider: "ProposalValidatorProvider",
    ):
        self.proposal_service = proposal_service
        self.dao_state_service = dao_state_service
        self.my_proposal_list_service = my_proposal_list_service
        self.bsq_wallet_service = bsq_wallet_service
        self.validator_provider = validator_provider

        dao_state_service.add_dao_state_listener(self)
        my_proposal_list_service.add_listener(self)

        self.all_proposals = ObservableList["Proposal"]()
        self.active_or_my_unconfirmed_proposals = FilteredList["Proposal"](
            self.all_proposals
        )

        self.proposal_list_change_listener = lambda e: self._update_lists()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        pass

    def start(self):
        # We must set the listeners initially and not on onParseBlockChainComplete as activeOrMyUnconfirmedProposals
        # is used in voteResults which can be called earlier during sync.
        # To avoid unneeded updateLists calls we delay one render frame so that once the proposalService is complete we
        # register our listeners.
        UserThread.execute(
            lambda: (
                self.proposal_service.temp_proposals.add_listener(
                    self.proposal_list_change_listener
                ),
                self.proposal_service.proposal_payloads.add_listener(
                    self.proposal_list_change_listener
                ),
            )
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_parse_block_complete_after_batch_processing(self, block: "Block"):
        self._update_lists()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // MyProposalListService.Listener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_list_changed(self, list: list["Proposal"]):
        self._update_lists()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _update_lists(self):
        temp_proposals = self.proposal_service.temp_proposals
        verified_proposals = {
            payload.proposal
            for payload in self.proposal_service.proposal_payloads
            if not self.dao_state_service.parse_block_chain_complete
            or self.validator_provider.get_validator(
                payload.proposal
            ).is_valid_and_confirmed(payload.proposal)
        }
        proposals_set = set(temp_proposals)
        proposals_set.update(verified_proposals)

        # We want to show our own unconfirmed proposals. Unconfirmed proposals from other users are not included
        # in the list.
        # If a tx is not found in the daoStateService it can be that it is either unconfirmed or invalid.
        # To avoid inclusion of invalid txs we add a check for the confidence type PENDING from the bsqWalletService.
        # So we only add proposals if they are unconfirmed and therefore not yet parsed. Once confirmed they have to be
        # found in the daoStateService.
        my_unconfirmed_proposals = []
        for proposal in self.my_proposal_list_service.list:
            if not self.dao_state_service.get_tx(
                proposal.tx_id
            ):  # Tx is still not in our bsq blocks
                tx_confidence = self.bsq_wallet_service.get_confidence_for_tx_id(
                    proposal.tx_id
                )
                if (
                    tx_confidence
                    and tx_confidence.confidence_type
                    == TransactionConfidenceType.PENDING
                ):
                    my_unconfirmed_proposals.append(proposal)
        proposals_set.update(my_unconfirmed_proposals)

        self.all_proposals.clear()
        self.all_proposals.extend(proposals_set)

        self.active_or_my_unconfirmed_proposals.filter = (
            lambda proposal: self.validator_provider.get_validator(
                proposal
            ).is_valid_and_confirmed(proposal)
            or proposal in my_unconfirmed_proposals
        )
