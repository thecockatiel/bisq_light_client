from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from bisq.core.network.p2p.direct_message import DirectMessage
from bisq.core.network.p2p.storage.payload.expirable_payload import ExpirablePayload
from bisq.core.network.p2p.uid_message import UidMessage

if TYPE_CHECKING:
    from bisq.core.network.p2p.node_address import NodeAddress

class MailboxMessage(DirectMessage, UidMessage, ExpirablePayload, ABC):
    
    @abstractmethod
    def get_sender_node_address(self) -> "NodeAddress":
        pass