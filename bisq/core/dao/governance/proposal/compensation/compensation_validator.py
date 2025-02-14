from typing import TYPE_CHECKING
from bisq.core.dao.governance.consensus_critical import ConsensusCritical
from bisq.core.dao.governance.proposal.compensation.compensation_consensus import (
    CompensationConsensus,
)
from bisq.core.dao.governance.proposal.proposal_validation_exception import (
    ProposalValidationException,
)
from bisq.core.dao.governance.proposal.proposal_validator import ProposalValidator
from bisq.core.dao.state.model.governance.compensation_proposal import (
    CompensationProposal,
)
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.dao.state.model.governance.proposal import Proposal
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.state.dao_state_service import DaoStateService


class CompensationValidator(ProposalValidator, ConsensusCritical):
    """Changes here can potentially break consensus!"""

    def __init__(
        self, dao_state_service: "DaoStateService", period_service: "PeriodService"
    ):
        super().__init__(dao_state_service, period_service)

    def validate_data_fields(self, proposal: "Proposal") -> None:
        try:
            super().validate_data_fields(proposal)

            if not isinstance(proposal, CompensationProposal):
                raise ProposalValidationException(
                    "Proposal must be of type CompensationProposal"
                )

            bsq_address = proposal.bsq_address
            check_argument(bsq_address, "bsq_address must not be empty")
            check_argument(bsq_address.startswith("B"), "bsq_address must start with B")
            proposal.get_address()  # throws AddressFormatException if wrong address

            requested_bsq = proposal.requested_bsq
            chain_height = self.get_block_height(proposal)
            max_compensation_request_amount = (
                CompensationConsensus.get_max_compensation_request_amount(
                    self.dao_state_service, chain_height
                )
            )
            check_argument(
                requested_bsq <= max_compensation_request_amount,
                f"Requested BSQ must not exceed {max_compensation_request_amount.value / 100} BSQ",
            )
            min_compensation_request_amount = (
                CompensationConsensus.get_min_compensation_request_amount(
                    self.dao_state_service, chain_height
                )
            )
            check_argument(
                requested_bsq >= min_compensation_request_amount,
                f"Requested BSQ must not be less than {min_compensation_request_amount.value / 100} BSQ",
            )
        except ProposalValidationException as e:
            raise e
        except Exception as e:
            raise ProposalValidationException(e)
