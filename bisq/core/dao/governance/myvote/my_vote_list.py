from typing import TYPE_CHECKING
from bisq.common.protocol.persistable.persistable_list import PersistableList
import pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.dao.governance.myvote.my_vote import MyVote


class MyVoteList(PersistableList["MyVote"]):
    def to_proto_message(self):
        return protobuf.PersistableEnvelope(
            my_vote_list=protobuf.MyVoteList(
                my_vote=[my_vote.to_proto_message() for my_vote in self.list]
            )
        )

    @staticmethod
    def from_proto(proto: protobuf.MyVoteList):
        return MyVoteList([MyVote.from_proto(p) for p in proto.my_vote])

    def __str__(self):
        return f"List of TxId's in MyVoteList: {[my_vote.blind_vote_tx_id for my_vote in self.list]}"
