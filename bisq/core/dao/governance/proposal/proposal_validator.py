from abc import ABC
from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.extra_data_map_validator import ExtraDataMapValidator
from bisq.core.dao.governance.consensus_critical import ConsensusCritical
from bisq.core.dao.governance.proposal.proposal_validation_exception import (
    ProposalValidationException,
)
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bisq.core.dao.state.model.governance.compensation_proposal import (
    CompensationProposal,
)
from bisq.core.dao.state.model.governance.dao_phase import DaoPhase
from bisq.core.dao.state.model.governance.reimbursement_proposal import (
    ReimbursementProposal,
)
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.model.governance.proposal import Proposal

logger = get_logger(__name__)


class ProposalValidator(ConsensusCritical, ABC):
    """Changes here can potentially break consensus!"""

    def __init__(
        self, dao_state_service: "DaoStateService", period_service: "PeriodService"
    ):
        self.dao_state_service = dao_state_service
        self.period_service = period_service

    def are_data_fields_valid(self, proposal: "Proposal") -> bool:
        try:
            self.validate_data_fields(proposal)
            return True
        except ProposalValidationException as e:
            logger.warning(
                f"Proposal data fields are invalid. proposal={proposal}, error={e}"
            )
            return False

    def validate_data_fields(self, proposal: "Proposal"):
        try:
            check_argument(proposal.name, "name must not be empty")
            check_argument(proposal.link, "link must not be empty")
            check_argument(len(proposal.name) <= 200, "name must not exceed 200 chars")
            check_argument(len(proposal.link) <= 200, "link must not exceed 200 chars")
            if proposal.tx_id is not None:
                check_argument(len(proposal.tx_id) == 64, "Tx ID must be 64 chars")

            ExtraDataMapValidator.validate(proposal.extra_data_map)
        except Exception as e:
            raise ProposalValidationException(e)

    def is_valid_or_unconfirmed(self, proposal: "Proposal") -> bool:
        return self._is_valid(proposal, True)

    def is_valid_and_confirmed(self, proposal: "Proposal") -> bool:
        return self._is_valid(proposal, False)

    def is_tx_type_valid(self, proposal: "Proposal") -> bool:
        tx_id = proposal.tx_id
        if not tx_id:
            logger.warning(f"tx_id must be set. proposal.tx_id={proposal.tx_id}")
            return False
        optional_tx_type = self.dao_state_service.get_optional_tx_type(tx_id)
        present = (
            optional_tx_type is not None and optional_tx_type == proposal.get_tx_type()
        )
        if not present:
            logger.debug(f"optional_tx_type not present for proposal {proposal}")
        return present

    def _is_valid(self, proposal: "Proposal", allow_unconfirmed: bool) -> bool:
        if not self.are_data_fields_valid(proposal):
            return False

        tx_id = proposal.tx_id
        if not tx_id:
            logger.warning(f"tx_id must be set. proposal.tx_id={proposal.tx_id}")
            return False

        optional_tx = self.dao_state_service.get_tx(tx_id)
        is_tx_confirmed = optional_tx is not None
        chain_height = self.dao_state_service.chain_height

        if is_tx_confirmed:
            tx_height = optional_tx.block_height
            if not self.period_service.is_tx_in_correct_cycle(tx_height, chain_height):
                logger.trace(
                    f"Tx is not in current cycle. proposal.tx_id={proposal.tx_id}"
                )
                return False
            if not self.period_service.is_in_phase(tx_height, DaoPhase.Phase.PROPOSAL):
                logger.debug(
                    f"Tx is not in PROPOSAL phase. proposal.tx_id={proposal.tx_id}"
                )
                return False
            if isinstance(proposal, CompensationProposal):
                if optional_tx.tx_type != TxType.COMPENSATION_REQUEST:
                    logger.error(
                        f"TxType is not a COMPENSATION_REQUEST. proposal.tx_id={proposal.tx_id}"
                    )
                    return False
            elif isinstance(proposal, ReimbursementProposal):
                if optional_tx.tx_type != TxType.REIMBURSEMENT_REQUEST:
                    logger.error(
                        f"TxType is not a REIMBURSEMENT_REQUEST. proposal.tx_id={proposal.tx_id}"
                    )
                    return False
            else:
                if optional_tx.tx_type != TxType.PROPOSAL:
                    logger.error(
                        f"TxType is not PROPOSAL. proposal.tx_id={proposal.tx_id}"
                    )
                    return False

            return True
        elif allow_unconfirmed:
            in_phase = self.period_service.is_in_phase(
                chain_height, DaoPhase.Phase.PROPOSAL
            )
            if in_phase:
                logger.debug(
                    f"proposal is unconfirmed and we are in proposal phase: tx_id={tx_id}"
                )
            return in_phase
        else:
            return False

    def get_block_height(self, proposal: "Proposal") -> int:
        # When we receive a temp proposal the tx is usually not confirmed so we cannot lookup the block height of
        # the tx. We take the current block height in that case as it would be in the same cycle anyway.
        tx = self.dao_state_service.get_tx(proposal.tx_id)
        if tx:
            return tx.block_height
        else:
            return self.dao_state_service.chain_height
