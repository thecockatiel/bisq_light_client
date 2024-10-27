from abc import ABC, abstractmethod

class ConnectionListener(ABC):

    @abstractmethod
    def on_connection(self, connection):
        pass

    @abstractmethod
    def on_disconnect(self, close_connection_reason, connection):
        pass