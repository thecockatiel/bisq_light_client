from abc import ABC, abstractmethod

from bisq.core.network.p2p.network.setup_listener import SetupListener


class P2PServiceListener(SetupListener, ABC):
    @abstractmethod
    def on_data_received(self):
        pass

    @abstractmethod
    def on_no_seed_node_available(self):
        pass

    @abstractmethod
    def on_no_peers_available(self):
        pass

    @abstractmethod
    def on_updated_data_received(self):
        pass
