from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.core.common.capabilities import Capabilities

class SupportedCapabilitiesListener(ABC):
    """
    Interface for objects that listen to changes in supported capabilities.
    """

    @abstractmethod
    def on_changed(self, supported_capabilities: 'Capabilities') -> None:
        pass