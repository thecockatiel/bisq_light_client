from abc import ABC, abstractmethod
from typing import Optional

class SetupListener(ABC):
    @abstractmethod
    def on_tor_node_ready(self) -> None:
        pass

    @abstractmethod
    def on_hidden_service_published(self) -> None:
        pass

    def on_setup_failed(self, raisable: Optional[Exception] = None) -> None:
        pass

    def on_request_custom_bridges(self) -> None:
        pass
