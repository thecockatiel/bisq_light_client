from bisq.core.dao.monitoring.model.blind_vote_state_hash import BlindVoteStateHash
from bisq.core.dao.monitoring.network.messages.new_state_hash_message import (
    NewStateHashMessage,
)
import pb_pb2 as protobuf


class NewBlindVoteStateHashMessage(NewStateHashMessage["BlindVoteStateHash"]):

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        builder = self.get_network_envelope_builder()
        builder.new_blind_vote_state_hash_message.CopyFrom(
            protobuf.NewBlindVoteStateHashMessage(
                state_hash=self.state_hash.to_proto_message()
            )
        )
        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.NewBlindVoteStateHashMessage, message_version: int
    ) -> "NewBlindVoteStateHashMessage":
        return NewBlindVoteStateHashMessage(
            BlindVoteStateHash.from_proto(proto.state_hash), message_version
        )

    def __str__(self) -> str:
        return (
            f"NewBlindVoteStateHashMessage{{\n     stateHash={self.state_hash}\n}} "
            + super().__str__()
        )
