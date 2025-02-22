from typing import TYPE_CHECKING

from bisq.core.dao.monitoring.network.messages.get_blind_vote_state_hashes_request import (
    GetBlindVoteStateHashesRequest,
)
from bisq.core.dao.monitoring.network.messages.get_blind_vote_state_hashes_response import (
    GetBlindVoteStateHashesResponse,
)
from bisq.core.dao.monitoring.network.messages.new_blind_vote_state_hash_message import (
    NewBlindVoteStateHashMessage,
)
from bisq.core.dao.monitoring.network.request_blind_vote_state_hashes_handler import (
    RequestBlindVoteStateHashesHandler,
)
from bisq.core.dao.monitoring.network.state_network_service import StateNetworkService
from bisq.core.exceptions.illegal_state_exception import IllegalStateException

if TYPE_CHECKING:
    from bisq.core.dao.monitoring.network.request_state_hashes_handler import (
        RequestStateHashesHandler,
    )
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.dao.monitoring.model.blind_vote_state_hash import BlindVoteStateHash


class BlindVoteStateNetworkService(
    StateNetworkService[
        "NewBlindVoteStateHashMessage",
        "GetBlindVoteStateHashesRequest",
        "GetBlindVoteStateHashesResponse",
        "RequestBlindVoteStateHashesHandler",
        "BlindVoteStateHash",
    ]
):
    def cast_to_get_state_hash_request(self, network_envelope):
        if isinstance(network_envelope, GetBlindVoteStateHashesRequest):
            return network_envelope
        else:
            raise IllegalStateException(
                f"Expected ian instance of GetBlindVoteStateHashesRequest but got {network_envelope.__class__.__name__}"
            )

    def is_get_state_hashes_request(self, network_envelope):
        return isinstance(network_envelope, GetBlindVoteStateHashesRequest)

    def cast_to_new_state_hash_message(self, network_envelope):
        if isinstance(network_envelope, NewBlindVoteStateHashMessage):
            return network_envelope
        else:
            raise IllegalStateException(
                f"Expected an instance of NewBlindVoteStateHashMessage but got {network_envelope.__class__.__name__}"
            )

    def is_new_state_hash_message(self, network_envelope):
        return isinstance(network_envelope, NewBlindVoteStateHashMessage)

    def get_get_state_hashes_response(
        self, nonce: int, state_hashes: list["BlindVoteStateHash"]
    ):
        return GetBlindVoteStateHashesResponse(
            state_hashes=state_hashes, request_nonce=nonce
        )

    def get_new_state_hash_message(self, my_state_hash: "BlindVoteStateHash"):
        return NewBlindVoteStateHashMessage(state_hash=my_state_hash)

    def get_request_state_hashes_handler(
        self,
        node_address: "NodeAddress",
        listener: "RequestStateHashesHandler.Listener[GetBlindVoteStateHashesResponse]",
    ):
        return RequestBlindVoteStateHashesHandler(
            self._network_node, self._peer_manager, node_address, listener
        )
