 
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.core.network.p2p.network.connection import Connection, NetworkEnvelope

class MessageListener(ABC):

    @abstractmethod
    def on_message(self, network_envelope: "NetworkEnvelope", connection: "Connection"):
        pass

    def on_message_sent(self, network_envelope: "NetworkEnvelope", connection: "Connection"):
        pass