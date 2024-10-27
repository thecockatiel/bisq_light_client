from abc import ABC, abstractmethod
from typing import Optional

from bisq.core.common.capabilities import Capabilities

class SupportedCapabilitiesMessage(ABC):
    
    @abstractmethod
    def get_supported_capabilities(self) -> Optional[Capabilities]:
        pass