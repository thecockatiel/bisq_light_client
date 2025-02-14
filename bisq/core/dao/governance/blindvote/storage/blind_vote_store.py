from typing import cast
from bisq.core.network.p2p.persistence.persistable_network_payload_store import (
    PersistableNetworkPayloadStore,
)
from bisq.core.dao.governance.blindvote.storage.blind_vote_payload import (
    BlindVotePayload,
)
import pb_pb2 as protobuf


class BlindVoteStore(PersistableNetworkPayloadStore["BlindVotePayload"]):
    """
    We store only the payload in the PB file to save disc space. The hash of the payload can be created anyway and
    is only used as key in the map. So we have a hybrid data structure which is represented as list in the protobuffer
    definition and provide a hashMap for the domain access.
    """

    def to_proto_message(self):
        return protobuf.PersistableEnvelope(
            blind_vote_store=protobuf.BlindVoteStore(
                items=[
                    cast(BlindVotePayload, item).to_proto_blind_vote_payload()
                    for item in self.map.values()
                ]
            )
        )

    @staticmethod
    def from_proto(proto: protobuf.BlindVoteStore) -> "BlindVoteStore":
        items = [BlindVotePayload.from_proto(item) for item in proto.items]
        return BlindVoteStore(items)
