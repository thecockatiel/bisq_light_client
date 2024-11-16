from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.common.capabilities import Capabilities

class HasCapabilities():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(self, 'capabilities'):
            raise RuntimeError(f"You need to have 'capabilities' in {self.__name__}")
