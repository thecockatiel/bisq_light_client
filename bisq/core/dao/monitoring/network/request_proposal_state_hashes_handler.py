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
from bisq.core.exceptions.illegal_state_exception import IllegalStateException


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
        if not isinstance(network_envelope, GetProposalStateHashesResponse):
            raise IllegalStateException(
                f"Expected an instance of GetProposalStateHashesResponse but got {network_envelope.__class__.__name__}"
            )
        return network_envelope

    def is_get_state_hashes_response(self, network_envelope: NetworkEnvelope) -> bool:
        return isinstance(network_envelope, GetProposalStateHashesResponse)
