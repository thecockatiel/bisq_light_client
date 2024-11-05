from abc import ABC, abstractmethod
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from bisq.core.network.p2p.network.connection import Connection
    from bisq.core.network.p2p.network.close_connection_reason import CloseConnectionReason

class ConnectionListener(ABC):

    @abstractmethod
    def on_connection(self, connection: 'Connection'):
        pass

    @abstractmethod
    def on_disconnect(self, close_connection_reason: 'CloseConnectionReason', connection: 'Connection'):
        pass