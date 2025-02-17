from typing import TYPE_CHECKING
from bisq.core.dao.governance.ballot.ballot_list_change_listener import (
    BallotListChangeListener,
)
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from utils.data import FilteredList, ObservableList

if TYPE_CHECKING:
    from bisq.core.dao.state.model.blockchain.block import Block
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.governance.proposal.proposal_validator_provider import (
        ProposalValidatorProvider,
    )
    from bisq.core.dao.governance.ballot.ballot_list_service import BallotListService
    from bisq.core.dao.state.model.governance.ballot import Ballot


class BallotListPresentation(BallotListChangeListener, DaoStateListener):
    """Provides the ballots as observableList for presentation classes."""

    def __init__(
        self,
        ballot_list_service: "BallotListService",
        period_service: "PeriodService",
        dao_state_service: "DaoStateService",
        proposal_validator_provider: "ProposalValidatorProvider",
    ):
        self._ballot_list_service = ballot_list_service
        self._period_service = period_service
        self._proposal_validator_provider = proposal_validator_provider

        self.all_ballots = ObservableList["Ballot"]()
        self.ballots_of_cycle = FilteredList["Ballot"](self.all_ballots)

        dao_state_service.add_dao_state_listener(self)
        ballot_list_service.add_listener(self)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_parse_block_complete_after_batch_processing(self, block: "Block"):
        self.ballots_of_cycle.set_filter(
            lambda ballot: self._period_service.is_tx_in_correct_cycle(
                ballot.tx_id, block.height
            )
        )
        self.on_list_changed(self._ballot_list_service.get_validated_ballot_list())

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // BallotListService.BallotListChangeListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_list_changed(self, list_: list["Ballot"]):
        self.all_ballots.clear()
        self.all_ballots.extend(list_)

    def get_all_valid_ballots(self) -> list["Ballot"]:
        return [
            ballot
            for ballot in self.all_ballots
            if (
                validator := self._proposal_validator_provider.get_validator(
                    ballot.proposal
                )
            ).are_data_fields_valid(ballot.proposal)
            and validator.is_tx_type_valid(ballot.proposal)
        ]
