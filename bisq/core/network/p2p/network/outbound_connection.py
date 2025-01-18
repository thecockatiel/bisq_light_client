from asyncio import StreamReader, StreamWriter
from typing import Optional, TYPE_CHECKING

from bisq.core.network.p2p.network.connection import Connection
from bisq.core.network.p2p.node_address import NodeAddress

if TYPE_CHECKING:
    from socket import socket as Socket
    from bisq.common.protocol.network.network_proto_resolver import (
        NetworkProtoResolver,
    )
    from bisq.core.network.p2p.network.ban_filter import BanFilter
    from bisq.core.network.p2p.network.connection_listener import ConnectionListener
    from bisq.core.network.p2p.network.message_listener import MessageListener


class OutboundConnection(Connection):
    def __init__(
        self,
        socket: tuple[StreamReader, StreamWriter],
        message_listener: "MessageListener",
        connection_listener: "ConnectionListener",
        peers_node_address: "NodeAddress",
        network_proto_resolver: "NetworkProtoResolver",
        ban_filter: Optional["BanFilter"] = None,
    ):
        super().__init__(
            socket=socket,
            message_listener=message_listener,
            connection_listener=connection_listener,
            peers_node_address=peers_node_address,
            network_proto_resolver=network_proto_resolver,
            ban_filter=ban_filter,
        )
