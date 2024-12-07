from typing import Optional, TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from bisq.common.capabilities import Capabilities

@runtime_checkable
class HasCapabilities(Protocol):
    capabilities: Optional['Capabilities']
