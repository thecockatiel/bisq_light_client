from bisq.core.dao.monitoring.network.messages.get_blind_vote_state_hashes_request import (
    GetBlindVoteStateHashesRequest,
)
from bisq.core.dao.monitoring.network.messages.get_state_hashes_response import (
    GetStateHashesResponse,
)
from bisq.core.dao.monitoring.model.blind_vote_state_hash import BlindVoteStateHash
import pb_pb2 as protobuf


class GetBlindVoteStateHashesResponse(GetStateHashesResponse["BlindVoteStateHash"]):

    def to_proto_network_envelope(self):
        builder = self.get_network_envelope_builder()
        builder.get_blind_vote_state_hashes_response.CopyFrom(
            protobuf.GetBlindVoteStateHashesResponse(
                state_hashes=[
                    state_hash.to_proto_message() for state_hash in self.state_hashes
                ],
                request_nonce=self.request_nonce,
            )
        )
        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.GetBlindVoteStateHashesResponse, message_version: int
    ) -> "GetBlindVoteStateHashesResponse":
        state_hashes = [
            BlindVoteStateHash.from_proto(state_hash)
            for state_hash in proto.state_hashes
        ]
        return GetBlindVoteStateHashesResponse(
            state_hashes=state_hashes,
            request_nonce=proto.request_nonce,
            message_version=message_version,
        )

    def associated_request(self):
        return GetBlindVoteStateHashesRequest
