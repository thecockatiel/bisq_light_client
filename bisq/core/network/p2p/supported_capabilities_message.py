from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.common.capabilities import Capabilities

class SupportedCapabilitiesMessage():
    supported_capabilities: Optional['Capabilities']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(self, "supported_capabilities"):
            raise RuntimeError(f"You need to have 'supported_capabilities' in {self.__name__}")
