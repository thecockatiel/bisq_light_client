from bisq.core.dao.monitoring.network.messages.get_state_hashes_request import (
    GetStateHashesRequest,
)
import pb_pb2 as protobuf


class GetBlindVoteStateHashesRequest(GetStateHashesRequest):

    def to_proto_network_envelope(self):
        builder = self.get_network_envelope_builder()
        builder.get_blind_vote_state_hashes_request.CopyFrom(
            protobuf.GetBlindVoteStateHashesRequest(
                height=self.height,
                nonce=self.nonce,
            )
        )
        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.GetBlindVoteStateHashesRequest, message_version: int
    ):
        return GetBlindVoteStateHashesRequest(
            height=proto.height,
            nonce=proto.nonce,
            message_version=message_version,
        )
