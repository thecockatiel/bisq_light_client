from abc import ABC, abstractmethod

from bisq.core.network.p2p.node_address import NodeAddress 

class SendersNodeAddressMessage(ABC):
    
    @abstractmethod
    def get_sender_node_address(self) -> NodeAddress:
        pass