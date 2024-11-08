from dataclasses import dataclass, field
from typing import Set, Iterable
from google.protobuf.message import Message

from bisq.core.common.protocol.persistable.persistable_envelope import PersistableEnvelope
import proto.pb_pb2 as protobuf 

from .peer import Peer

@dataclass
class PeerList(PersistableEnvelope):
    set: frozenset[Peer] = field(default=frozenset())

    def size(self) -> int:
        return len(self.set)

    def to_proto_message(self) -> Message:
        peer_list_proto = protobuf.PeerList()
        peer_list_proto.peer.extend([peer.to_proto_message() for peer in self.set])
        
        envelope_proto = protobuf.PersistableEnvelope(
            peer_list=peer_list_proto
        )
        
        return envelope_proto

    @staticmethod
    def from_proto(proto: protobuf.PeerList) -> 'PeerList':
        peers = {Peer.from_proto(peer_proto) for peer_proto in proto.peer}
        return PeerList(peers)

    def set_all(self, collection: Iterable[Peer]) -> None:
        self.set = frozenset(collection)

    def __str__(self) -> str:
        return f"PeerList{{\n     set={self.set}\n}}"

    def __eq__(self, other) -> bool:
        if not isinstance(other, PeerList):
            return False
        return self.set == other.set

    def __hash__(self) -> int:
        return None