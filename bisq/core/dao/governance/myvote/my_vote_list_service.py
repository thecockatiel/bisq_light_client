from collections.abc import Callable
from typing import TYPE_CHECKING
from bisq.common.crypto.encryption import Encryption
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.common.setup.log_setup import get_logger
from bisq.core.dao.governance.myvote.my_vote_list import MyVoteList
from bisq.core.dao.governance.myvote.my_vote import MyVote

if TYPE_CHECKING:
    from bisq.core.dao.governance.blindvote.my_blind_vote_list_service import (
        MyBlindVoteListService,
    )
    from bisq.core.dao.governance.blindvote.blind_vote import BlindVote
    from bisq.core.dao.state.model.governance.ballot_list import BallotList
    from bisq.common.persistence.persistence_manager import PersistenceManager
    from bisq.core.dao.state.dao_state_service import DaoStateService

logger = get_logger(__name__)


class MyVoteListService(PersistedDataHost):
    """Creates and stores myVote items. Persist in MyVoteList."""

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        persistence_manager: "PersistenceManager[MyVoteList]",
    ):
        self._dao_state_service = dao_state_service
        self._persistence_manager = persistence_manager
        self._my_vote_list = MyVoteList()

        self._persistence_manager.initialize(
            self._my_vote_list, PersistenceManagerSource.PRIVATE
        )

    @property
    def my_vote_list(self):
        return self._my_vote_list

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PersistedDataHost
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def read_persisted(self, complete_handler: Callable[[], None]) -> None:
        def on_persisted(persisted: "MyVoteList") -> None:
            self._my_vote_list.set_all(persisted.list)
            complete_handler()

        self._persistence_manager.read_persisted(on_persisted, complete_handler)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def create_and_add_my_vote(
        self,
        sorted_ballot_list_for_cycle: "BallotList",
        secret_key: bytes,
        blind_vote: "BlindVote",
    ):
        my_vote = MyVote(
            self._dao_state_service.chain_height,
            sorted_ballot_list_for_cycle,
            secret_key,
            blind_vote,
        )
        logger.info(f"Add new MyVote to myVotesList list.\nMyVote={my_vote}")
        self._my_vote_list.append(my_vote)
        self._request_persistence()

    def apply_reveal_tx_id(self, my_vote: "MyVote", vote_reveal_tx_id: str) -> None:
        my_vote.reveal_tx_id = vote_reveal_tx_id
        logger.debug(
            f"Applied revealTxId to myVote.\nmyVote={my_vote}\nvoteRevealTxId={vote_reveal_tx_id}"
        )
        self._request_persistence()

    def get_merit_and_stake_for_proposal(
        self, proposal_tx_id: str, my_blind_vote_list_service: "MyBlindVoteListService"
    ) -> tuple[int, int]:
        merit = 0
        stake = 0
        vote_list = sorted(self._my_vote_list.list, key=lambda vote: vote.date)
        for my_vote in vote_list:
            for ballot in my_vote.ballot_list.list:
                if ballot.tx_id == proposal_tx_id:
                    merit = my_vote.get_merit(
                        my_blind_vote_list_service, self._dao_state_service
                    )
                    stake = my_vote.blind_vote.stake
                    break
        return merit, stake

    def get_my_vote_list_for_cycle(self) -> list["MyVote"]:
        current_cycle = self._dao_state_service.current_cycle
        if current_cycle is None:
            return []
        return [
            vote
            for vote in self._my_vote_list.list
            if current_cycle.is_in_cycle(vote.height)
        ]

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _request_persistence(self) -> None:
        self._persistence_manager.request_persistence()
