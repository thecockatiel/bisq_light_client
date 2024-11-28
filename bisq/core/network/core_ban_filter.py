from collections.abc import Callable
from bisq.core.network.p2p.node_address import NodeAddress

class CoreBanFilter:
    def __init__(self, ban_list: list[str]):
        self.banned_peers_from_options = set(NodeAddress(addr) for addr in ban_list)
        self.banned_node_predicate: Callable[[NodeAddress], bool] = None

    def set_banned_node_predicate(self, banned_node_predicate: Callable[[NodeAddress], bool]):
        self.banned_node_predicate = banned_node_predicate

    def is_peer_banned(self, node_address):
        return (node_address in self.banned_peers_from_options or
                (self.banned_node_predicate is not None and self.banned_node_predicate(node_address)))


