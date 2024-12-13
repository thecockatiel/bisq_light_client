from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from bisq.core.network.p2p.direct_message import DirectMessage
from bisq.core.network.p2p.storage.payload.expirable_payload import ExpirablePayload
from bisq.core.network.p2p.uid_message import UidMessage

if TYPE_CHECKING:
    from bisq.core.network.p2p.node_address import NodeAddress

@runtime_checkable
class _MailboxMessageProtocol(Protocol):
    sender_node_address: "NodeAddress"


class MailboxMessage(DirectMessage, UidMessage, ExpirablePayload, _MailboxMessageProtocol, ABC):
    sender_node_address: "NodeAddress"