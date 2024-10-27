 
from abc import ABC, abstractmethod

from bisq.core.network.p2p.network.connection import Connection, NetworkEnvelope

class MessageListener(ABC):

    @abstractmethod
    def on_message(self, network_envelope: NetworkEnvelope, connection: Connection):
        pass

    @abstractmethod
    def on_message_sent(self, network_envelope: NetworkEnvelope, connection: Connection):
        pass