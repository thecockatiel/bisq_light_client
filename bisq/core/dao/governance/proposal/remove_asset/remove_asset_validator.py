from typing import TYPE_CHECKING
from bisq.core.dao.governance.consensus_critical import ConsensusCritical

from bisq.core.dao.governance.proposal.proposal_validation_exception import (
    ProposalValidationException,
)
from bisq.core.dao.governance.proposal.proposal_validator import ProposalValidator
from bisq.core.dao.state.model.governance.remove_asset_proposal import (
    RemoveAssetProposal,
)
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.model.governance.proposal import Proposal


class RemoveAssetValidator(ProposalValidator, ConsensusCritical):
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

            if not isinstance(proposal, RemoveAssetProposal):
                raise ProposalValidationException(
                    "Proposal must be of type RemoveAssetProposal"
                )

            check_argument(
                proposal.ticker_symbol,
                "TickerSymbol must not be empty",
            )

            #  We want to avoid that someone causes damage by inserting a super long string. Real ticker symbols
            #  are usually very short but we don't want to add additional restrictions here.
            check_argument(
                len(proposal.ticker_symbol) <= 100,
                "TickerSymbol must not exceed 100 chars",
            )
        except ProposalValidationException as e:
            raise e
        except Exception as e:
            raise ProposalValidationException(e)
