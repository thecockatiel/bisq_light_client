from bisq.core.dao.monitoring.model.proposal_state_hash import ProposalStateHash
from bisq.core.dao.monitoring.network.messages.new_state_hash_message import (
    NewStateHashMessage,
)
import pb_pb2 as protobuf


class NewProposalStateHashMessage(NewStateHashMessage["ProposalStateHash"]):

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        builder = self.get_network_envelope_builder()
        builder.new_proposal_state_hash_message.CopyFrom(
            protobuf.NewProposalStateHashMessage(
                state_hash=self.state_hash.to_proto_message()
            )
        )
        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.NewProposalStateHashMessage, message_version: int
    ) -> "NewProposalStateHashMessage":
        return NewProposalStateHashMessage(
            ProposalStateHash.from_proto(proto.state_hash), message_version
        )

    def __str__(self) -> str:
        return (
            f"NewProposalStateHashMessage{{\n     stateHash={self.state_hash}\n}} "
            + super().__str__()
        )
