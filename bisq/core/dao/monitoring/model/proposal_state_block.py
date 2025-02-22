from typing import TYPE_CHECKING
from bisq.core.dao.monitoring.model.state_block import StateBlock

if TYPE_CHECKING:
    from bisq.core.dao.monitoring.model.proposal_state_hash import ProposalStateHash


class ProposalStateBlock(StateBlock["ProposalStateHash"]):

    @property
    def num_proposals(self) -> int:
        return self.my_state_hash.num_proposals
