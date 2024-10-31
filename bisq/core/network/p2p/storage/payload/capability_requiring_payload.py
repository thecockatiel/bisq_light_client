from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Set

from bisq.core.common.protocol.network.network_payload import NetworkPayload 

if TYPE_CHECKING:
    from bisq.core.common.capability import Capability

class CapabilityRequiringPayload(NetworkPayload, ABC):
    """
    Used for payloads which requires certain capability.

    This is used for TradeStatistics to be able to support old versions which don't know about that class.
    We only send the data to nodes which are capable to handle that data (e.g. TradeStatistics supported from v. 0.4.9.1 on).
    """
    
    @abstractmethod
    def get_required_capabilities(self) -> 'Set[Capability]':
        """
        Returns the capabilities the other node needs to support to receive that message.
        """
        pass