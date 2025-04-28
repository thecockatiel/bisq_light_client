from typing import TYPE_CHECKING
from bisq.core.dao.governance.consensus_critical import ConsensusCritical

from bisq.core.dao.governance.proposal.proposal_validation_exception import (
    ProposalValidationException,
)
from bisq.core.dao.governance.proposal.proposal_validator import ProposalValidator
from bisq.core.dao.state.model.governance.role_proposal import RoleProposal
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.model.governance.proposal import Proposal


class RoleValidator(ProposalValidator, ConsensusCritical):
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

            if not isinstance(proposal, RoleProposal):
                raise ProposalValidationException(
                    "Proposal must be of type RoleProposal"
                )

            check_argument(proposal.role is not None, "Bonded role must not be None")
        except Exception as e:
            raise ProposalValidationException(e)
