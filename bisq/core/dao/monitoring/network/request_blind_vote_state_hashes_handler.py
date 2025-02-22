from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.dao.monitoring.network.request_state_hashes_handler import (
    RequestStateHashesHandler,
)
from bisq.core.dao.monitoring.network.messages.get_blind_vote_state_hashes_request import (
    GetBlindVoteStateHashesRequest,
)
from bisq.core.dao.monitoring.network.messages.get_blind_vote_state_hashes_response import (
    GetBlindVoteStateHashesResponse,
)
from bisq.core.exceptions.illegal_state_exception import IllegalStateException


class RequestBlindVoteStateHashesHandler(
    RequestStateHashesHandler[
        GetBlindVoteStateHashesRequest, GetBlindVoteStateHashesResponse
    ]
):

    def get_get_state_hashes_request(
        self, from_height: int
    ) -> GetBlindVoteStateHashesRequest:
        return GetBlindVoteStateHashesRequest(height=from_height, nonce=self.nonce)

    def cast_to_get_state_hashes_response(
        self, network_envelope: NetworkEnvelope
    ) -> "GetBlindVoteStateHashesResponse":
        if not isinstance(network_envelope, GetBlindVoteStateHashesResponse):
            raise IllegalStateException(
                f"Expected an instance of GetBlindVoteStateHashesResponse but got {network_envelope.__class__.__name__}"
            )
        return network_envelope

    def is_get_state_hashes_response(self, network_envelope: NetworkEnvelope) -> bool:
        return isinstance(network_envelope, GetBlindVoteStateHashesResponse)
