from collections.abc import Callable
import logging
from typing import TYPE_CHECKING, Optional
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.common.setup.log_setup import get_logger
from bisq.core.dao.dao_setup_service import DaoSetupService
from utils.concurrency import ThreadSafeSet
from bisq.core.dao.state.model.governance.ballot_list import BallotList
from utils.data import ObservableChangeEvent, ObservableList
from bisq.core.dao.governance.proposal.storage.appendonly.proposal_payload import (
    ProposalPayload,
)
from bisq.core.dao.state.model.governance.ballot import Ballot

if TYPE_CHECKING:
    from bisq.core.dao.state.model.governance.proposal import Proposal
    from bisq.common.persistence.persistence_manager import PersistenceManager
    from bisq.core.dao.governance.ballot.ballot_list_change_listener import (
        BallotListChangeListener,
    )
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.governance.proposal.proposal_service import ProposalService
    from bisq.core.dao.governance.proposal.proposal_validator_provider import (
        ProposalValidatorProvider,
    )
    from bisq.core.dao.state.model.governance.vote import Vote


logger = get_logger(__name__)


class BallotListService(PersistedDataHost, DaoSetupService):
    """
    Takes the proposals from the append only store and makes Ballots out of it (vote is null).
    Applies voting on individual ballots and persist the list.
    The BallotList contains all ballots of all cycles.
    """

    def __init__(
        self,
        proposal_service: "ProposalService",
        period_service: "PeriodService",
        validator_provider: "ProposalValidatorProvider",
        persistence_manager: "PersistenceManager[BallotList]",
    ):
        self.proposal_service = proposal_service
        self.period_service = period_service
        self.validator_provider = validator_provider
        self.persistence_manager = persistence_manager

        self.ballot_list = BallotList()
        self.listeners = ThreadSafeSet["BallotListChangeListener"]()

        self.persistence_manager.initialize(
            self.ballot_list, PersistenceManagerSource.NETWORK
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        payloads = self.proposal_service.proposal_payloads
        payloads.add_listener(self._on_changed)

    def _on_changed(self, e: ObservableChangeEvent["ProposalPayload"]) -> None:
        if e.added_elements:
            for payload in e.added_elements:
                proposal = payload.proposal
                if self._is_new_proposal(proposal):
                    self._register_proposal_as_ballot(proposal)
            self._request_persistence()

    def _is_new_proposal(self, proposal: "Proposal") -> bool:
        return all(ballot.proposal != proposal for ballot in self.ballot_list)

    def _register_proposal_as_ballot(self, proposal: "Proposal") -> None:
        ballot = Ballot(proposal)  # vote is None
        if logger.isEnabledFor(logging.INFO):  # TODO: JAVA SANITY CHECK
            logger.debug(
                "We create a new ballot with a proposal and add it to our list. "
                f"Vote is None at that moment. proposalTxId={proposal.tx_id}"
            )
        if ballot in self.ballot_list:
            logger.warning(f"Ballot {ballot} already exists on our ballotList")
        else:
            self.ballot_list.append(ballot)
            for listener in self.listeners:
                listener.on_list_changed(self.ballot_list.list)

    def start(self) -> None:
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PersistedDataHost
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def read_persisted(self, complete_handler: Callable[[], None]) -> None:
        def on_persisted_read(persisted: "BallotList") -> None:
            self.ballot_list.set_all(persisted.list)
            for listener in self.listeners:
                listener.on_list_changed(self.ballot_list.list)
            complete_handler()

        self.persistence_manager.read_persisted(on_persisted_read, complete_handler)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def set_vote(self, ballot: "Ballot", vote: Optional["Vote"]) -> None:
        ballot.vote = vote
        self._request_persistence()

    def add_listener(self, listener: "BallotListChangeListener") -> None:
        self.listeners.add(listener)

    def get_validated_ballot_list(self) -> list["Ballot"]:
        return [
            ballot
            for ballot in self.ballot_list
            if self.validator_provider.get_validator(ballot.proposal).is_tx_type_valid(
                ballot.proposal
            )
        ]

    def get_valid_ballots_of_cycle(self) -> list["Ballot"]:
        return [
            ballot
            for ballot in self.ballot_list
            if self.validator_provider.get_validator(ballot.proposal).is_tx_type_valid(
                ballot.proposal
            )
            and self.period_service.is_tx_in_correct_cycle(
                ballot.tx_id, self.period_service.chain_height
            )
        ]

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _request_persistence(self) -> None:
        self.persistence_manager.request_persistence()
