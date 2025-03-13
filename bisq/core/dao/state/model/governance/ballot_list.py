from bisq.common.protocol.persistable.persistable_list import PersistableList
from bisq.core.dao.governance.consensus_critical import ConsensusCritical
from bisq.core.dao.state.model.governance.ballot import Ballot
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
import pb_pb2 as protobuf


class BallotList(PersistableList[Ballot], ConsensusCritical, ImmutableDaoStateModel):
    """PersistableEnvelope wrapper for list of ballots."""

    def to_proto_message(self):
        return protobuf.PersistableEnvelope(
            ballot_list=protobuf.BallotList(
                ballot=[ballot.to_proto_message() for ballot in self]
            )
        )

    @staticmethod
    def from_proto(proto: protobuf.BallotList):
        return BallotList(
            [Ballot.from_proto(ballot_proto) for ballot_proto in proto.ballot]
        )

    def __str__(self):
        return "BallotList: " + str([ballot.info() for ballot in self])
    
    def __eq__(self, value):
        return isinstance(value, BallotList) and self.list == value.list
    
    def __hash__(self):
        # wrong but we do it anyway
        return hash(tuple(self.list))
