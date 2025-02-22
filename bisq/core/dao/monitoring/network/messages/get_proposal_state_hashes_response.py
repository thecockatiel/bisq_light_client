from bisq.core.dao.monitoring.network.messages.get_proposal_state_hashes_request import (
    GetProposalStateHashesRequest,
)
from bisq.core.dao.monitoring.network.messages.get_state_hashes_response import (
    GetStateHashesResponse,
)
from bisq.core.dao.monitoring.model.proposal_state_hash import ProposalStateHash
import pb_pb2 as protobuf


class GetProposalStateHashesResponse(GetStateHashesResponse["ProposalStateHash"]):

    def to_proto_network_envelope(self):
        builder = self.get_network_envelope_builder()
        builder.get_proposal_state_hashes_response.CopyFrom(
            protobuf.GetProposalStateHashesResponse(
                state_hashes=[
                    state_hash.to_proto_message() for state_hash in self.state_hashes
                ],
                request_nonce=self.request_nonce,
            )
        )
        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.GetProposalStateHashesResponse, message_version: int
    ) -> "GetProposalStateHashesResponse":
        state_hashes = [
            ProposalStateHash.from_proto(state_hash)
            for state_hash in proto.state_hashes
        ]
        return GetProposalStateHashesResponse(
            state_hashes=state_hashes,
            request_nonce=proto.request_nonce,
            message_version=message_version,
        )

    def associated_request(self):
        return GetProposalStateHashesRequest
