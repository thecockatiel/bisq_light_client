from typing import Collection, List, cast
from bisq.core.account.sign.signed_witness import SignedWitness
from bisq.core.network.p2p.persistence.persistable_network_payload_store import PersistableNetworkPayloadStore
import proto.pb_pb2 as protobuf


class SignedWitnessStore(PersistableNetworkPayloadStore[SignedWitness]):
    
    def __init__(self, collection: Collection[SignedWitness] | None = None) -> None:
        super().__init__(collection)

    def to_proto_message(self):
        return protobuf.PersistableEnvelope(signed_witness_store=self.get_builder())

    def get_builder(self):
        proto_list = [cast(SignedWitness, payload).to_proto_signed_witness() for payload in self.map.values()]
        return protobuf.SignedWitnessStore(items=proto_list)

    @staticmethod
    def from_proto(proto: protobuf.SignedWitnessStore):
        list = [SignedWitness.from_proto(item) for item in proto.items]
        return SignedWitnessStore(list)


