from typing import TYPE_CHECKING

from bisq.common.setup.log_setup import get_logger
from bisq.common.util.math_utils import MathUtils
from bisq.core.dao.state.model.governance.compensation_proposal import (
    CompensationProposal,
)
from bisq.core.dao.state.model.governance.dao_phase import DaoPhase
from bisq.core.dao.state.model.governance.issuance import Issuance
from bisq.core.dao.state.model.governance.issuance_type import IssuanceType
from bisq.core.dao.state.model.governance.reimbursement_proposal import (
    ReimbursementProposal,
)
from utils.preconditions import check_argument


if TYPE_CHECKING:
    from bisq.core.dao.governance.proposal.issuance_proposal import IssuanceProposal
    from bisq.core.dao.state.model.blockchain.tx_output import TxOutput
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.state.dao_state_service import DaoStateService


logger = get_logger(__name__)


class IssuanceService:

    def __init__(
        self, dao_state_service: "DaoStateService", period_service: "PeriodService"
    ):
        self._dao_state_service = dao_state_service
        self._period_service = period_service

    def issue_bsq(self, issuance_proposal: "IssuanceProposal", chain_height: int):
        for tx_output in self._dao_state_service.get_issuance_candidate_tx_outputs():
            if self._is_valid(tx_output, issuance_proposal, chain_height):
                issuance_type = IssuanceType.UNDEFINED
                if isinstance(issuance_proposal, CompensationProposal):
                    issuance_type = IssuanceType.COMPENSATION
                elif isinstance(issuance_proposal, ReimbursementProposal):
                    issuance_type = IssuanceType.REIMBURSEMENT
                check_argument(
                    issuance_type != IssuanceType.UNDEFINED,
                    "issuanceType must not be undefined",
                )

                # We don't check atm if the output is unspent. We cannot use the bsqWallet as that would not
                # reflect our current block state (could have been spent at later block which is valid and
                # bsqWallet would show that spent state). We would need to support a spent status for the outputs
                # which are interpreted as BTC (as a not yet accepted comp. request).
                tx = self._dao_state_service.get_tx(issuance_proposal.get_tx_id())
                check_argument(tx is not None, "tx must be present")
                amount = issuance_proposal.get_requested_bsq().value
                # We use key from first input
                tx_input = tx.tx_inputs[0]
                pub_key = tx_input.pub_key
                issuance = Issuance(tx.id, chain_height, amount, pub_key, issuance_type)
                self._dao_state_service.add_issuance(issuance)
                self._dao_state_service.add_unspent_tx_output(tx_output)

                sb = []
                sb.append(
                    "\n################################################################################\n"
                )
                sb.append(f"We issued new BSQ to tx with ID {tx_output.tx_id}")
                sb.append(
                    f"\nIssued BSQ: {MathUtils.scale_down_by_power_of_10(amount, 2)}"
                )
                sb.append(f"\nIssuance type: {issuance_type.name}")
                sb.append(
                    "\n################################################################################\n"
                )
                logger.info("".join(sb))

    def _is_valid(
        self,
        tx_output: "TxOutput",
        issuance_proposal: "IssuanceProposal",
        chain_height: int,
    ) -> bool:
        return (
            tx_output.tx_id == issuance_proposal.get_tx_id()
            and issuance_proposal.get_requested_bsq().value == tx_output.value
            and issuance_proposal.get_bsq_address()[1:] == tx_output.address
            and self._period_service.is_tx_in_phase_and_cycle(
                tx_output.tx_id, DaoPhase.Phase.PROPOSAL, chain_height
            )
        )
