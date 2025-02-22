from typing import TYPE_CHECKING
from bisq.core.dao.monitoring.model.state_block import StateBlock

if TYPE_CHECKING:
    from bisq.core.dao.monitoring.model.blind_vote_state_hash import BlindVoteStateHash


class BlindVoteStateBlock(StateBlock["BlindVoteStateHash"]):

    @property
    def num_blind_votes(self) -> int:
        return self.my_state_hash.num_blind_votes
