from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.core.network.p2p.decrypted_message_with_pub_key import (
        DecryptedMessageWithPubKey,
    )
    from bisq.core.network.p2p.node_address import NodeAddress


class DecryptedMailboxListener(ABC):
    @abstractmethod
    def on_mailbox_message_added(
        decrypted_message_with_pub_key: "DecryptedMessageWithPubKey",
        sender_node_address: "NodeAddress",
    ) -> None:
        pass
