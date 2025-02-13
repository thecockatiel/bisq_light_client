from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
from bisq.core.dao.state.model.governance.proposal_vote_result import ProposalVoteResult
import pb_pb2 as protobuf


class EvaluatedProposal(PersistablePayload, ImmutableDaoStateModel):

    def __init__(self, is_accepted: bool, proposal_vote_result: ProposalVoteResult):
        self._is_accepted = is_accepted
        self._proposal_vote_result = proposal_vote_result

    @property
    def is_accepted(self):
        return self._is_accepted

    @property
    def proposal_vote_result(self):
        return self._proposal_vote_result

    def to_proto_message(self) -> protobuf.EvaluatedProposal:
        builder = protobuf.EvaluatedProposal(
            is_accepted=self._is_accepted,
            proposal_vote_result=self._proposal_vote_result.to_proto_message(),
        )
        return builder

    @staticmethod
    def from_proto(proto: protobuf.EvaluatedProposal) -> "EvaluatedProposal":
        return EvaluatedProposal(
            is_accepted=proto.is_accepted,
            proposal_vote_result=ProposalVoteResult.from_proto(
                proto.proposal_vote_result
            ),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @property
    def proposal(self):
        return self._proposal_vote_result.proposal

    @property
    def proposal_tx_id(self):
        return self.proposal.tx_id

    def __str__(self):
        return (
            f"EvaluatedProposal{{\n"
            f"    is_accepted={self._is_accepted},\n"
            f"    proposal_vote_result={self._proposal_vote_result}\n"
            f"}}"
        )
