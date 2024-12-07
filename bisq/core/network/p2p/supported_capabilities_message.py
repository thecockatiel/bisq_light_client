from typing import Optional, TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from bisq.common.capabilities import Capabilities

@runtime_checkable
class SupportedCapabilitiesMessage(Protocol):
    supported_capabilities: Optional['Capabilities']

