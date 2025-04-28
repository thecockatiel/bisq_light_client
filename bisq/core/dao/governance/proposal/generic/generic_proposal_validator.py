from typing import TYPE_CHECKING
from bisq.core.dao.governance.consensus_critical import ConsensusCritical

from bisq.core.dao.governance.proposal.proposal_validation_exception import (
    ProposalValidationException,
)
from bisq.core.dao.governance.proposal.proposal_validator import ProposalValidator

if TYPE_CHECKING:
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.model.governance.proposal import Proposal


class GenericProposalValidator(ProposalValidator, ConsensusCritical):
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
        except ProposalValidationException as e:
            raise e
        except Exception as e:
            raise ProposalValidationException(e)
