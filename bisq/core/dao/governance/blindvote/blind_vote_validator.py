from typing import TYPE_CHECKING

from bisq.common.setup.log_setup import get_logger
from bisq.common.util.extra_data_map_validator import ExtraDataMapValidator
from bisq.core.btc.wallet.restrictions import Restrictions
from bisq.core.dao.governance.proposal.proposal_validation_exception import (
    ProposalValidationException,
)
from bisq.core.dao.state.model.governance.dao_phase import DaoPhase
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.dao.governance.blindvote.blind_vote import BlindVote
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.state.dao_state_service import DaoStateService


logger = get_logger(__name__)


class BlindVoteValidator:

    def __init__(
        self, dao_state_service: "DaoStateService", period_service: "PeriodService"
    ):
        self.dao_state_service = dao_state_service
        self.period_service = period_service

    def are_data_fields_valid(self, blind_vote: "BlindVote") -> bool:
        try:
            self._validate_data_fields(blind_vote)
            return True
        except Exception:
            return False

    def _validate_data_fields(self, blind_vote: "BlindVote") -> None:
        try:
            check_argument(
                blind_vote.encrypted_votes is not None,
                "encrypted_votes must not be None",
            )
            check_argument(
                len(blind_vote.encrypted_votes) > 0, "encrypted_votes must not be empty"
            )
            check_argument(
                len(blind_vote.encrypted_votes) <= 100000,
                "encrypted_votes must not exceed 100kb",
            )

            check_argument(blind_vote.tx_id is not None, "Tx ID must not be None")
            check_argument(len(blind_vote.tx_id) == 64, "Tx ID must be 64 chars")
            check_argument(
                blind_vote.stake >= Restrictions.get_min_non_dust_output().value,
                "Stake must be at least MinNonDustOutput",
            )

            check_argument(
                blind_vote.encrypted_merit_list is not None,
                "encrypted_merit_list must not be None",
            )
            check_argument(
                len(blind_vote.encrypted_merit_list) > 0,
                "encrypted_merit_list must not be empty",
            )
            check_argument(
                len(blind_vote.encrypted_merit_list) <= 100000,
                "encrypted_merit_list must not exceed 100kb",
            )

            ExtraDataMapValidator.validate(blind_vote.extra_data_map)
        except Exception as e:
            logger.warning(str(e))
            raise ProposalValidationException(e)

    def are_data_fields_valid_and_tx_confirmed(self, blind_vote: "BlindVote") -> bool:
        if not self.are_data_fields_valid(blind_vote):
            logger.warning(f"blindVote is invalid. blindVote={blind_vote}")
            return False

        # Check if tx is already confirmed and in DaoState
        is_confirmed = self.dao_state_service.get_tx(blind_vote.tx_id) is not None
        if self.dao_state_service.parse_block_chain_complete and not is_confirmed:
            logger.warning(
                f"blindVoteTx is not confirmed. blindVoteTxId={blind_vote.tx_id}"
            )

        return is_confirmed

    def is_tx_in_phase_and_cycle(self, blind_vote: "BlindVote") -> bool:
        tx_id = blind_vote.tx_id
        optional_tx = self.dao_state_service.get_tx(tx_id)
        if not optional_tx:
            logger.debug(f"Tx is not in daoStateService. blindVoteTxId={tx_id}")
            return False

        tx_height = optional_tx.block_height
        if not self.period_service.is_tx_in_correct_cycle(
            tx_height, self.dao_state_service.chain_height
        ):
            logger.debug(f"Tx is not in current cycle. blindVote={blind_vote}")
            return False

        if not self.period_service.is_tx_in_phase(tx_id, DaoPhase.Phase.BLIND_VOTE):
            logger.debug(f"Tx is not in BLIND_VOTE phase. blindVote={blind_vote}")
            return False

        return True
