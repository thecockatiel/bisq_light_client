from typing import TYPE_CHECKING, Optional, TypeVar

from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.network.p2p.network.connection import Connection
    from bisq.core.dao.monitoring.network.messages.get_state_hashes_response import (
        GetStateHashesResponse,
    )

_Res = TypeVar("Res", bound="GetStateHashesResponse")


class RequestStateHashesHandlerListener(ABC):
    @abstractmethod
    def on_complete(
        self, get_state_hashes_response: _Res, peers_node_address: Optional["NodeAddress"]
    ) -> None:
        pass

    @abstractmethod
    def on_fault(self, error_message: str, connection: Optional["Connection"]) -> None:
        pass
