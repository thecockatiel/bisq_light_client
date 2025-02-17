from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.core.dao.state.model.governance.proposal import Proposal
    from bitcoinj.core.transaction import Transaction


@dataclass(frozen=True)
class ProposalWithTransaction:
    proposal: "Proposal"
    transaction: "Transaction"
