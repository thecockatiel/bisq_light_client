from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.core.network.p2p.decrypted_message_with_pub_key import (
        DecryptedMessageWithPubKey,
    )
    from bisq.core.network.p2p.node_address import NodeAddress


class DecryptedDirectMessageListener(ABC):
    def on_direct_message(
        self,
        decrypted_message_with_pub_key: "DecryptedMessageWithPubKey",
        peer_node_address: "NodeAddress",
    ):
        pass
