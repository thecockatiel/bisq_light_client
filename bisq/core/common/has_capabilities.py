from abc import ABC, abstractmethod
from .capabilities import Capabilities

class HasCapabilities(ABC):
    """
    Holds a set of Capabilities.

    Author: Florian Reimair
    """

    @abstractmethod
    def get_capabilities(self) -> Capabilities:
        pass