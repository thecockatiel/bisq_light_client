from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from bisq.core.common.protocol.network.network_payload import NetworkPayload

if TYPE_CHECKING:
    from bisq.core.network.p2p.node_address import NodeAddress


class RequiresOwnerIsOnlinePayload(NetworkPayload, ABC):
    @abstractmethod
    def get_owner_node_address(self) -> "NodeAddress":
        pass
