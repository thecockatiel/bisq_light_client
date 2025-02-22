from typing import TYPE_CHECKING

from bisq.core.dao.monitoring.network.messages.get_proposal_state_hashes_request import (
    GetProposalStateHashesRequest,
)
from bisq.core.dao.monitoring.network.messages.get_proposal_state_hashes_response import (
    GetProposalStateHashesResponse,
)
from bisq.core.dao.monitoring.network.messages.new_proposal_state_hash_message import (
    NewProposalStateHashMessage,
)
from bisq.core.dao.monitoring.network.request_proposal_state_hashes_handler import (
    RequestProposalStateHashesHandler,
)
from bisq.core.dao.monitoring.network.state_network_service import StateNetworkService
from bisq.core.exceptions.illegal_state_exception import IllegalStateException

if TYPE_CHECKING:
    from bisq.core.dao.monitoring.network.request_state_hashes_handler import (
        RequestStateHashesHandler,
    )
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.dao.monitoring.model.proposal_state_hash import ProposalStateHash


class ProposalStateNetworkService(
    StateNetworkService[
        "NewProposalStateHashMessage",
        "GetProposalStateHashesRequest",
        "GetProposalStateHashesResponse",
        "RequestProposalStateHashesHandler",
        "ProposalStateHash",
    ]
):
    def cast_to_get_state_hash_request(self, network_envelope):
        if isinstance(network_envelope, GetProposalStateHashesRequest):
            return network_envelope
        else:
            raise IllegalStateException(
                f"Expected ian instance of GetProposalStateHashesRequest but got {network_envelope.__class__.__name__}"
            )

    def is_get_state_hashes_request(self, network_envelope):
        return isinstance(network_envelope, GetProposalStateHashesRequest)

    def cast_to_new_state_hash_message(self, network_envelope):
        if isinstance(network_envelope, NewProposalStateHashMessage):
            return network_envelope
        else:
            raise IllegalStateException(
                f"Expected an instance of NewProposalStateHashMessage but got {network_envelope.__class__.__name__}"
            )

    def is_new_state_hash_message(self, network_envelope):
        return isinstance(network_envelope, NewProposalStateHashMessage)

    def get_get_state_hashes_response(
        self, nonce: int, state_hashes: list["ProposalStateHash"]
    ):
        return GetProposalStateHashesResponse(
            state_hashes=state_hashes, request_nonce=nonce
        )

    def get_new_state_hash_message(self, my_state_hash: "ProposalStateHash"):
        return NewProposalStateHashMessage(state_hash=my_state_hash)

    def get_request_state_hashes_handler(
        self,
        node_address: "NodeAddress",
        listener: "RequestStateHashesHandler.Listener[GetProposalStateHashesResponse]",
    ):
        return RequestProposalStateHashesHandler(
            self._network_node, self._peer_manager, node_address, listener
        )
