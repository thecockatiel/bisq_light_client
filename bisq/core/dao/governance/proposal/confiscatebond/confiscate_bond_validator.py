from typing import TYPE_CHECKING
from bisq.core.dao.governance.consensus_critical import ConsensusCritical

from bisq.core.dao.governance.proposal.proposal_validation_exception import (
    ProposalValidationException,
)
from bisq.core.dao.governance.proposal.proposal_validator import ProposalValidator
from bisq.core.dao.state.model.governance.confiscate_bond_proposal import (
    ConfiscateBondProposal,
)
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.model.governance.proposal import Proposal


class ConfiscateBondValidator(ProposalValidator, ConsensusCritical):
    """Changes here can potentially break consensus!"""

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        period_service: "PeriodService",
    ):
        super().__init__(dao_state_service, period_service)

    def validate_data_fields(self, proposal: "Proposal") -> None:
        try:
            super().validate_data_fields(proposal)
            confiscate_bond_proposal = proposal
            if not isinstance(confiscate_bond_proposal, ConfiscateBondProposal):
                raise ProposalValidationException(
                    "Proposal is not an instance of ConfiscateBondProposal"
                )
            check_argument(
                confiscate_bond_proposal.lockup_tx_id, "LockupTxId must not be empty"
            )
            check_argument(
                len(confiscate_bond_proposal.lockup_tx_id) == 64,
                "LockupTxId must be 64 chars",
            )
        except ProposalValidationException as e:
            raise e
        except Exception as e:
            raise ProposalValidationException(e)
