from typing import Optional
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.dao.governance.consensus_critical import ConsensusCritical
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
from bisq.core.dao.state.model.governance.proposal import Proposal
from bisq.core.dao.state.model.governance.vote import Vote
import pb_pb2 as protobuf


class Ballot(PersistablePayload, ConsensusCritical, ImmutableDaoStateModel):
    """
    Base class for all ballots like compensation request, generic request, remove asset ballots and
    change param ballots.
    It contains the Proposal and the Vote. If a Proposal is ignored for voting the vote object is null.

    One proposal has about 278 bytes
    """

    def __init__(self, proposal: Proposal, vote: Optional[Vote] = None):
        self.proposal = proposal
        self.vote = vote

    def to_proto_message(self) -> protobuf.Ballot:
        builder = protobuf.Ballot(proposal=self.proposal.to_proto_message())
        if self.vote:
            builder.vote.CopyFrom(self.vote.to_proto_message())
        return builder

    @staticmethod
    def from_proto(proto: protobuf.Ballot) -> "Ballot":
        proposal = Proposal.from_proto(proto.proposal)
        vote = Vote.from_proto(proto.vote) if proto.HasField("vote") else None
        return Ballot(proposal, vote)

    @property
    def tx_id(self):
        return self.proposal.tx_id

    def __str__(self):
        return (
            "Ballot{\n"
            f"     proposal={self.proposal},\n"
            f"     vote={self.vote}\n"
            "}"
        )

    def info(self):
        return (
            "Ballot{\n"
            f"     proposalTxId={self.proposal.tx_id},\n"
            f"     vote={self.vote}\n"
            "}"
        )

    def __eq__(self, value):
        if not isinstance(value, Ballot):
            return False
        return self.proposal == value.proposal and self.vote == value.vote

    def __hash__(self):
        return hash((self.proposal, self.vote))
