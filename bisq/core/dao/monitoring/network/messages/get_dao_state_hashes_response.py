from bisq.core.dao.monitoring.network.messages.get_dao_state_hashes_request import (
    GetDaoStateHashesRequest,
)
from bisq.core.dao.monitoring.network.messages.get_state_hashes_response import (
    GetStateHashesResponse,
)
from bisq.core.dao.monitoring.model.dao_state_hash import DaoStateHash
import pb_pb2 as protobuf


class GetDaoStateHashesResponse(GetStateHashesResponse["DaoStateHash"]):

    def to_proto_network_envelope(self):
        builder = self.get_network_envelope_builder()
        builder.get_dao_state_hashes_response.CopyFrom(
            protobuf.GetDaoStateHashesResponse(
                state_hashes=[
                    state_hash.to_proto_message() for state_hash in self.state_hashes
                ],
                request_nonce=self.request_nonce,
            )
        )
        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.GetDaoStateHashesResponse, message_version: int
    ) -> "GetDaoStateHashesResponse":
        state_hashes = [
            DaoStateHash.from_proto(state_hash) for state_hash in proto.state_hashes
        ]
        return GetDaoStateHashesResponse(
            state_hashes=state_hashes,
            request_nonce=proto.request_nonce,
            message_version=message_version,
        )

    def associated_request(self):
        return GetDaoStateHashesRequest
