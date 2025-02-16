from typing import TYPE_CHECKING

from bisq.core.dao.monitoring.network.state_network_service import StateNetworkService
from bisq.core.dao.monitoring.network.messages.get_dao_state_hashes_request import (
    GetDaoStateHashesRequest,
)
from bisq.core.dao.monitoring.network.messages.new_dao_state_hash_message import (
    NewDaoStateHashMessage,
)
from bisq.core.dao.monitoring.network.request_dao_state_hashes_handler import (
    RequestDaoStateHashesHandler,
)
from bisq.core.dao.monitoring.network.messages.get_dao_state_hashes_response import (
    GetDaoStateHashesResponse,
)
from bisq.core.exceptions.illegal_state_exception import IllegalStateException

if TYPE_CHECKING:
    from bisq.core.dao.monitoring.network.request_state_hashes_handler import RequestStateHashesHandler
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.dao.monitoring.model.dao_state_hash import DaoStateHash


class DaoStateNetworkService(
    StateNetworkService[
        "NewDaoStateHashMessage",
        "GetDaoStateHashesRequest",
        "GetDaoStateHashesResponse",
        "RequestDaoStateHashesHandler",
        "DaoStateHash",
    ]
):
    def cast_to_get_state_hash_request(self, network_envelope):
        if isinstance(network_envelope, GetDaoStateHashesRequest):
            return network_envelope
        else:
            raise IllegalStateException(
                f"Expected ian instance of GetDaoStateHashesRequest but got {network_envelope.__class__.__name__}"
            )

    def is_get_state_hashes_request(self, network_envelope):
        return isinstance(network_envelope, GetDaoStateHashesRequest)

    def cast_to_new_state_hash_message(self, network_envelope):
        if isinstance(network_envelope, NewDaoStateHashMessage):
            return network_envelope
        else:
            raise IllegalStateException(
                f"Expected an instance of NewDaoStateHashMessage but got {network_envelope.__class__.__name__}"
            )

    def is_new_state_hash_message(self, network_envelope):
        return isinstance(network_envelope, NewDaoStateHashMessage)

    def get_get_state_hashes_response(
        self, nonce: int, state_hashes: list["DaoStateHash"]
    ):
        return GetDaoStateHashesResponse(state_hashes=state_hashes, request_nonce=nonce)

    def get_new_state_hash_message(self, my_state_hash: "DaoStateHash"):
        return NewDaoStateHashMessage(state_hash=my_state_hash)

    def get_request_state_hashes_handler(
        self,
        node_address: "NodeAddress",
        listener: "RequestStateHashesHandler.Listener[GetDaoStateHashesResponse]",
    ):
        return RequestDaoStateHashesHandler(
            self._network_node, self._peer_manager, node_address, listener
        )
