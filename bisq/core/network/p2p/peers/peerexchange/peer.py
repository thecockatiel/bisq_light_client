from google.protobuf.message import Message

from datetime import datetime
from dataclasses import dataclass, field

from bisq.core.common.capabilities import Capabilities
from bisq.core.common.has_capabilities import HasCapabilities
from bisq.core.common.protocol.network.network_payload import NetworkPayload
from bisq.core.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.network.p2p.network.supported_capabilities_listener import SupportedCapabilitiesListener
from bisq.core.network.p2p.node_address import NodeAddress

import proto.pb_pb2 as protobuf


@dataclass
class Peer(HasCapabilities, NetworkPayload, PersistablePayload, SupportedCapabilitiesListener):
    MAX_FAILED_CONNECTION_ATTEMPTS: int = 5

    node_address: NodeAddress
    date: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    _failed_connection_attempts: int = field(default=0, init=False, repr=False)
    capabilities: Capabilities = field(default_factory=Capabilities)

    def to_proto_message(self) -> protobuf.Peer:
        peer_proto = protobuf.Peer(
            node_address=self.node_address.to_proto_message(),
            date=self.date,
            supported_capabilities=Capabilities.to_int_list(self.capabilities)
        )
        return peer_proto

    @classmethod
    def from_proto(cls, proto: protobuf.Peer) -> 'Peer':
        node_address = NodeAddress.from_proto(proto)
        capabilities = Capabilities.from_int_list(proto.supported_capabilities)
        return cls(node_address=node_address, date=proto.date, capabilities=capabilities)

    def on_disconnect(self) -> None:
        self._failed_connection_attempts += 1

    def on_connection(self) -> None:
        self._failed_connection_attempts = max(self._failed_connection_attempts - 1, 0)

    def too_many_failed_connection_attempts(self) -> bool:
        return self._failed_connection_attempts >= self.MAX_FAILED_CONNECTION_ATTEMPTS

    def on_changed(self, supported_capabilities: Capabilities) -> None:
        if not supported_capabilities.is_empty():
            self.capabilities.set(supported_capabilities)

    @property
    def failed_connection_attempts(self) -> int:
        return self._failed_connection_attempts

    @failed_connection_attempts.setter
    def failed_connection_attempts(self, value: int) -> None:
        self._failed_connection_attempts = value

    def get_date(self) -> datetime:
        return datetime.fromtimestamp(self.date / 1000)

    def get_date_as_long(self) -> int:
        return self.date

    def __eq__(self, other) -> bool:
        if not isinstance(other, Peer):
            return False
        return self.node_address == other.node_address

    def __hash__(self) -> int:
        return hash(self.node_address) if self.node_address else 0

    def __str__(self) -> str:
        return (
            f"Peer{{\n"
            f"     node_address={self.node_address},\n"
            f"     date={self.date},\n"
            f"     failed_connection_attempts={self._failed_connection_attempts},\n"
            f"     capabilities={self.capabilities}\n"
            f"}}"
        )