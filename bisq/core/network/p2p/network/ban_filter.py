from abc import ABC, abstractmethod 
from typing import Callable

from bisq.core.network.p2p.node_address import NodeAddress

class BanFilter(ABC):
    @abstractmethod
    def is_peer_banned(self, node_address: NodeAddress) -> bool:
        pass

    @abstractmethod
    def set_banned_node_predicate(self, is_node_address_banned: Callable[[NodeAddress], bool]) -> None:
        pass