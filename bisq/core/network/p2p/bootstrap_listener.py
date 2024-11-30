from abc import ABC, abstractmethod
from typing import Optional
from bisq.core.network.p2p.p2p_service_listener import P2PServiceListener


class BootstrapListener(P2PServiceListener, ABC):
 
    def on_tor_node_ready(self) -> None:
        pass

    def on_hidden_service_published(self) -> None:
        pass

    def on_no_seed_node_available(self):
        pass

    def on_no_peers_available(self):
        pass
    
    def on_setup_failed(self, exception: Optional[Exception] = None) -> None:
        pass
    
    def on_updated_data_received(self):
        pass

    @abstractmethod
    def on_data_received(self):
        pass

    def on_request_custom_bridges(self) -> None:
        pass


