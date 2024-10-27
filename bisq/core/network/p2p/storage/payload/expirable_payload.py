from abc import ABC, abstractmethod

from bisq.core.common.protocol.network.network_payload import NetworkPayload

class ExpirablePayload(NetworkPayload, ABC):
    """
    Messages which support a time to live

    Implementations:
    
    - ProtectedStoragePayload
    - MailboxStoragePayload
    """

    @abstractmethod
    def get_ttl(self) -> int:
        """
        @return Time to live in milli seconds
        """
        pass