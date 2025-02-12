from bisq.common.protocol.persistable.persistable_list import PersistableList
from bisq.core.dao.governance.proofofburn.my_proof_of_burn import MyProofOfBurn
import pb_pb2 as protobuf


class MyProofOfBurnList(PersistableList["MyProofOfBurn"]):
    """PersistableEnvelope wrapper for list of MyProofOfBurn objects."""

    def __init__(self, collection: list[MyProofOfBurn] = None):
        super().__init__(collection)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self) -> protobuf.PersistableEnvelope:
        builder = protobuf.PersistableEnvelope(my_proof_of_burn_list=self.get_builder())
        return builder

    def get_builder(self):
        return protobuf.MyProofOfBurnList(
            my_proof_of_burn=[x.to_proto_message() for x in self.list]
        )

    @staticmethod
    def from_proto(proto: protobuf.MyProofOfBurnList) -> "MyProofOfBurnList":
        return MyProofOfBurnList(
            collection=[MyProofOfBurn.from_proto(x) for x in proto.my_proof_of_burn]
        )

    def __str__(self) -> str:
        tx_ids = [x.tx_id for x in self.list]
        return f"List of txIds in MyProofOfBurnList: {tx_ids}"
