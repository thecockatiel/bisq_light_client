from typing import Collection, Optional, cast
from bisq.core.account.witness.account_age_witness import AccountAgeWitness
from bisq.core.network.p2p.persistence.persistable_network_payload_store import PersistableNetworkPayloadStore
import proto.pb_pb2 as protobuf

# We store only the payload in the PB file to save disc space. The hash of the payload can be created anyway and
# is only used as key in the map. So we have a hybrid data structure which is represented as list in the protobuffer
# definition and provide a hashMap for the domain access.
class AccountAgeWitnessStore(PersistableNetworkPayloadStore[AccountAgeWitness]):
    
    def __init__(self, collection: Optional[Collection[AccountAgeWitness]] = None) -> None:
        super().__init__(collection)

    def to_proto_message(self):
        return protobuf.PersistableEnvelope(account_age_witness_store=self.get_builder())

    def get_builder(self):
        proto_list = [payload.to_proto_account_age_witness() for payload in self.map.values() if isinstance(payload, AccountAgeWitness)]
        return protobuf.AccountAgeWitnessStore(items=proto_list)

    @staticmethod
    def from_proto(proto: protobuf.AccountAgeWitnessStore):
        list = [AccountAgeWitness.from_proto(item) for item in proto.items]
        return AccountAgeWitnessStore(list)
