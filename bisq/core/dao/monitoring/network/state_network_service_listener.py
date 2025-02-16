from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar
from typing import Optional


if TYPE_CHECKING:
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.network.p2p.network.connection import Connection
    from bisq.core.dao.monitoring.model.state_hash import StateHash
    from bisq.core.dao.monitoring.network.messages.get_state_hashes_request import (
        GetStateHashesRequest,
    )
    from bisq.core.dao.monitoring.network.messages.new_state_hash_message import (
        NewStateHashMessage,
    )

Msg = TypeVar("Msg", bound="NewStateHashMessage")
Req = TypeVar("Req", bound="GetStateHashesRequest")
StH = TypeVar("StH", bound="StateHash")


class StateNetworkServiceListener(Generic[Msg, Req, StH], ABC):

    @abstractmethod
    def on_new_state_hash_message(
        self, new_state_hash_message: Msg, connection: "Connection"
    ) -> None:
        pass

    @abstractmethod
    def on_get_state_hash_request(
        self, connection: "Connection", get_state_hash_request: Req
    ) -> None:
        pass

    @abstractmethod
    def on_peers_state_hashes(
        self, state_hashes: list[StH], peers_node_address: Optional["NodeAddress"]
    ) -> None:
        pass
