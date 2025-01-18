from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.mailbox.mailbox_message import MailboxMessage
from bisq.core.network.p2p.uid_message import UidMessage
from bisq.core.support.support_type import SupportType
from utils.data import raise_required

@dataclass
class SupportMessage(NetworkEnvelope, MailboxMessage, UidMessage, ABC):
    uid: str = field(default_factory=raise_required)
    # Added with v1.1.6. Old clients will not have set that field and we fall back to entry 0 which is ARBITRATION.
    support_type: 'SupportType' = field(default_factory=raise_required)

    @abstractmethod
    def get_trade_id(self) -> str:
        pass

    def __str__(self) -> str:
        return (f"DisputeMessage{{\n"
                f"     uid='{self.uid}',\n"
                f"     messageVersion={self.message_version},\n"
                f"     supportType={self.support_type}\n"
                f"}} {super().__str__()}")
