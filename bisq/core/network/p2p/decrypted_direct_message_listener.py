from abc import ABC
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.core.network.p2p.decrypted_message_with_pub_key import (
        DecryptedMessageWithPubKey,
    )
    from bisq.core.network.p2p.node_address import NodeAddress


class DecryptedDirectMessageListener(
    Callable[["DecryptedMessageWithPubKey", "NodeAddress"], None], ABC
):
    def on_direct_message(
        self,
        decrypted_message_with_pub_key: "DecryptedMessageWithPubKey",
        peer_node_address: "NodeAddress",
    ):
        pass
    
    def __call__(
        self,
        decrypted_message_with_pub_key: "DecryptedMessageWithPubKey",
        peer_node_address: "NodeAddress",
    ):
        self.on_direct_message(decrypted_message_with_pub_key, peer_node_address)