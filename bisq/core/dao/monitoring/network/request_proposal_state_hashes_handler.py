from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.dao.monitoring.network.request_state_hashes_handler import (
    RequestStateHashesHandler,
)
from bisq.core.dao.monitoring.network.messages.get_proposal_state_hashes_request import (
    GetProposalStateHashesRequest,
)
from bisq.core.dao.monitoring.network.messages.get_proposal_state_hashes_response import (
    GetProposalStateHashesResponse,
)


class RequestProposalStateHashesHandler(
    RequestStateHashesHandler[
        GetProposalStateHashesRequest, GetProposalStateHashesResponse
    ]
):

    def get_get_state_hashes_request(
        self, from_height: int
    ) -> GetProposalStateHashesRequest:
        return GetProposalStateHashesRequest(height=from_height, nonce=self.nonce)

    def cast_to_get_state_hashes_response(
        self, network_envelope: NetworkEnvelope
    ) -> "GetProposalStateHashesResponse":
        return network_envelope

    def is_get_state_hashes_response(self, network_envelope: NetworkEnvelope) -> bool:
        return isinstance(network_envelope, GetProposalStateHashesResponse)
