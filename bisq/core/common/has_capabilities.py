from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.core.common.capabilities import Capabilities

class HasCapabilities():
    capabilities: Optional['Capabilities']

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "capabilities"):
            raise RuntimeError(f"You need to have 'capabilities' in {cls.__name__}")
