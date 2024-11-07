from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope

if TYPE_CHECKING:
    from bisq.core.support.support_type import SupportType

 
@dataclass(frozen=True, kw_only=True)
class SupportMessage(NetworkEnvelope, ABC):
    uid: str
    # Added with v1.1.6. Old clients will not have set that field and we fall back to entry 0 which is ARBITRATION.
    support_type: 'SupportType' 

    @abstractmethod
    def get_trade_id(self) -> str:
        pass

    def __str__(self) -> str:
        return (f"DisputeMessage{{\n"
                f"     uid='{self.uid}',\n"
                f"     messageVersion={self.message_version},\n"
                f"     supportType={self.support_type}\n"
                f"}} {super().__str__()}")