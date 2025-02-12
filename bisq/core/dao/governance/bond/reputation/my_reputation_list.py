from bisq.common.protocol.persistable.persistable_list import PersistableList
from bisq.core.dao.governance.bond.reputation.my_reputation import MyReputation
import pb_pb2 as protobuf


class MyReputationList(PersistableList["MyReputation"]):
    """PersistableEnvelope wrapper for list of MyReputations"""

    def __init__(self, collection: list["MyReputation"] = None):
        super().__init__(collection)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self) -> protobuf.PersistableEnvelope:
        return protobuf.PersistableEnvelope(my_reputation_list=self.get_builder())

    def get_builder(self) -> protobuf.MyReputationList:
        builder = protobuf.MyReputationList(
            my_reputation=[reputation.to_proto_message() for reputation in self]
        )
        return builder

    @staticmethod
    def from_proto(proto: protobuf.MyReputationList) -> "MyReputationList":
        reputations = [
            MyReputation.from_proto(reputation) for reputation in proto.my_reputation
        ]
        return MyReputationList(reputations)

    def __str__(self) -> str:
        salts = [reputation.salt for reputation in self]
        return f"List of salts in MyReputationList: {salts}"
