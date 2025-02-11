from bisq.common.crypto.hash import get_ripemd160_hash
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.dao.governance.consensus_critical import ConsensusCritical
from bisq.core.network.p2p.storage.payload.persistable_network_payload import (
    PersistableNetworkPayload,
)
from bisq.core.dao.state.model.governance.proposal import Proposal
import pb_pb2 as protobuf


class ProposalPayload(PersistableNetworkPayload, ConsensusCritical):

    def __init__(self, proposal: "Proposal", hash: bytes = None):
        if hash is None:
            hash = get_ripemd160_hash(proposal.serialize_for_hash())
        self.proposal = proposal
        self.hash = hash  # 20 byte

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_proposal_builder(self):
        builder = protobuf.ProposalPayload(
            proposal=self.proposal.to_proto_message(),
            hash=self.hash,
        )
        return builder

    def to_proto_message(self):
        return protobuf.PersistableNetworkPayload(
            proposal_payload=self.get_proposal_builder()
        )

    def to_proto_proposal_payload(self):
        return self.get_proposal_builder()

    @staticmethod
    def from_proto(proto: protobuf.ProposalPayload) -> "ProposalPayload":
        return ProposalPayload(
            proposal=Proposal.from_proto(proto.proposal),
            hash=proto.hash,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PersistableNetworkPayload
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def verify_hash_size(self) -> bool:
        return len(self.hash) == 20

    def get_hash(self) -> bytes:
        return self.hash

    def __str__(self):
        return (
            f"ProposalPayload{{\n"
            f"    proposal={self.proposal},\n"
            f"    hash={bytes_as_hex_string(self.hash)}\n"
            f"}}"
        )
