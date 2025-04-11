from typing import TYPE_CHECKING
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.common.setup.log_setup import get_logger
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
import pb_pb2 as protobuf
from utils.preconditions import check_argument
from bisq.core.dao.state.model.governance.proposal import Proposal

logger = get_logger(__name__)


class ProposalVoteResult(PersistablePayload, ImmutableDaoStateModel):
    def __init__(
        self,
        proposal: "Proposal",
        stake_of_accepted_votes: int,
        stake_of_rejected_votes: int,
        num_accepted_votes: int,
        num_rejected_votes: int,
        num_ignored_votes: int,
    ):
        self._proposal = proposal
        self._stake_of_accepted_votes = stake_of_accepted_votes
        self._stake_of_rejected_votes = stake_of_rejected_votes
        self._num_accepted_votes = num_accepted_votes
        self._num_rejected_votes = num_rejected_votes
        self._num_ignored_votes = num_ignored_votes

    @property
    def proposal(self) -> "Proposal":
        return self._proposal

    @property
    def stake_of_accepted_votes(self) -> int:
        return self._stake_of_accepted_votes

    @property
    def stake_of_rejected_votes(self) -> int:
        return self._stake_of_rejected_votes

    @property
    def num_accepted_votes(self) -> int:
        return self._num_accepted_votes

    @property
    def num_rejected_votes(self) -> int:
        return self._num_rejected_votes

    @property
    def num_ignored_votes(self) -> int:
        return self._num_ignored_votes

    def to_proto_message(self):
        return protobuf.ProposalVoteResult(
            proposal=self._proposal.to_proto_message(),
            stake_of_accepted_votes=self._stake_of_accepted_votes,
            stake_of_rejected_votes=self._stake_of_rejected_votes,
            num_accepted_votes=self._num_accepted_votes,
            num_rejected_votes=self._num_rejected_votes,
            num_ignored_votes=self._num_ignored_votes,
        )

    @staticmethod
    def from_proto(proto: protobuf.ProposalVoteResult):
        return ProposalVoteResult(
            proposal=Proposal.from_proto(proto.proposal),
            stake_of_accepted_votes=proto.stake_of_accepted_votes,
            stake_of_rejected_votes=proto.stake_of_rejected_votes,
            num_accepted_votes=proto.num_accepted_votes,
            num_rejected_votes=proto.num_rejected_votes,
            num_ignored_votes=proto.num_ignored_votes,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @property
    def num_active_votes(self) -> int:
        return self._num_accepted_votes + self._num_rejected_votes

    @property
    def _total_stake(self) -> int:
        return self._stake_of_accepted_votes + self._stake_of_rejected_votes

    @property
    def quorum(self) -> int:
        # Quorum is sum of all votes independent if accepted or rejected.
        logger.debug(
            f"Quorum: proposalTxId: {self._proposal.tx_id}, "
            f"totalStake: {self._total_stake}, "
            f"stakeOfAcceptedVotes: {self._stake_of_accepted_votes}, "
            f"stakeOfRejectedVotes: {self._stake_of_rejected_votes}"
        )
        return self._total_stake

    @property
    def threshold(self) -> int:
        check_argument(
            self._stake_of_accepted_votes >= 0,
            "stake_of_accepted_votes must not be negative",
        )
        check_argument(
            self._stake_of_rejected_votes >= 0,
            "stake_of_rejected_votes must not be negative",
        )
        if self._stake_of_accepted_votes == 0:
            return 0
        return self._stake_of_accepted_votes * 10_000 // self._total_stake

    def __str__(self) -> str:
        return (
            f"ProposalVoteResult{{\n"
            f"     proposal={self._proposal},\n"
            f"     stake_of_accepted_votes={self._stake_of_accepted_votes},\n"
            f"     stake_of_rejected_votes={self._stake_of_rejected_votes},\n"
            f"     num_accepted_votes={self._num_accepted_votes},\n"
            f"     num_rejected_votes={self._num_rejected_votes},\n"
            f"     num_ignored_votes={self._num_ignored_votes}\n"
            f"}}"
        )
