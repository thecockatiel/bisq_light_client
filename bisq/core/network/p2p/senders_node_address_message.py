
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from bisq.core.network.p2p.node_address import NodeAddress 

@runtime_checkable
class SendersNodeAddressMessage(Protocol):
    sender_node_address: "NodeAddress"