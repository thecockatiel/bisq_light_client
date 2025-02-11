from typing import TYPE_CHECKING, Optional
from bisq.common.crypto.hash import get_ripemd160_hash
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.dao.governance.consensus_critical import ConsensusCritical
from bisq.core.network.p2p.storage.payload.persistable_network_payload import (
    PersistableNetworkPayload,
)
from bisq.core.dao.governance.blindvote.blind_vote import BlindVote
import pb_pb2 as protobuf


class BlindVotePayload(PersistableNetworkPayload, ConsensusCritical):
    """
    Wrapper for proposal to be stored in the append-only BlindVoteStore storage.

    Data size: 185 bytes
    """

    def __init__(self, blind_vote: BlindVote, hash: Optional[bytes] = None):
        self.blind_vote = blind_vote
        if hash is None:
            hash = get_ripemd160_hash(blind_vote.serialize_for_hash())
        self.hash = hash

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_blind_vote_builder(self):
        builder = protobuf.BlindVotePayload(
            blind_vote=self.blind_vote.to_proto_message(),
            hash=self.hash,
        )
        return builder

    def to_proto_message(self):
        return protobuf.PersistableNetworkPayload(
            blind_vote_payload=self.get_blind_vote_builder()
        )

    def to_proto_blind_vote_payload(self):
        return self.get_blind_vote_builder()

    @staticmethod
    def from_proto(proto: protobuf.BlindVotePayload) -> "BlindVotePayload":
        return BlindVotePayload(BlindVote.from_proto(proto.blind_vote), proto.hash)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PersistableNetworkPayload
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def verify_hash_size(self) -> bool:
        return len(self.hash) == 20

    def get_hash(self) -> bytes:
        return self.hash

    def __str__(self) -> str:
        return (
            f"BlindVotePayload{{\n"
            f"     blind_vote={self.blind_vote},\n"
            f"     hash={bytes_as_hex_string(self.hash)}\n"
            f"}}"
        )
