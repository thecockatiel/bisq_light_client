from bisq.common.protocol.persistable.persistable_list import PersistableList
from bisq.core.dao.governance.blindvote.blind_vote import BlindVote
from bisq.core.dao.governance.consensus_critical import ConsensusCritical
import pb_pb2 as protobuf


class MyBlindVoteList(PersistableList["BlindVote"], ConsensusCritical):
    """List of my own blind votes. Blind votes received from other voters are stored in the BlindVoteStore."""

    def to_proto_message(self):
        return protobuf.PersistableEnvelope(
            my_blind_vote_list=protobuf.MyBlindVoteList(
                blind_vote=[vote.to_proto_message() for vote in self]
            )
        )

    @staticmethod
    def from_proto(proto: protobuf.MyBlindVoteList):
        return MyBlindVoteList(
            [BlindVote.from_proto(vote) for vote in proto.blind_vote]
        )

    def __str__(self):
        return f"MyBlindVoteList: {[vote.tx_id for vote in self]}"
