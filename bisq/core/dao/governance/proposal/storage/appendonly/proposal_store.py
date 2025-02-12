from typing import cast
from bisq.core.network.p2p.persistence.persistable_network_payload_store import (
    PersistableNetworkPayloadStore,
)
from bisq.core.dao.governance.proposal.storage.appendonly.proposal_payload import (
    ProposalPayload,
)
import pb_pb2 as protobuf


class ProposalStore(PersistableNetworkPayloadStore["ProposalPayload"]):
    """
    We store only the payload in the PB file to save disc space. The hash of the payload can be created anyway and
    is only used as key in the map. So we have a hybrid data structure which is represented as list in the protobuffer
    definition and provide a hashMap for the domain access.
    """

    def to_proto_message(self):
        return protobuf.PersistableEnvelope(proposal_store=self.get_builder())

    def get_builder(self):
        return protobuf.ProposalStore(
            items=[
                cast(ProposalPayload, payload).to_proto_proposal_payload()
                for payload in self.map.values()
            ]
        )

    @staticmethod
    def from_proto(proto: protobuf.ProposalStore) -> "ProposalStore":
        return ProposalStore([ProposalPayload.from_proto(item) for item in proto.items])
