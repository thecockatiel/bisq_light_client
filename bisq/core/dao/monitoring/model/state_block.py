from abc import ABC
from typing import TYPE_CHECKING, Generic, TypeVar


if TYPE_CHECKING:
    from bisq.core.dao.monitoring.model.state_hash import StateHash


_T = TypeVar("T", bound="StateHash")


class StateBlock(Generic[_T], ABC):
    """
    Contains my StateHash at a particular block height and the received stateHash from our peers.
    The maps get updated over time, this is not an immutable class.
    """

    def __init__(self, my_state_hash: _T):
        self.my_state_hash = my_state_hash
        self.peers_map: dict[str, _T] = {}
        self.in_conflict_map: dict[str, _T] = {}

    def put_in_peers_map(self, peers_node_address: str, state_hash: _T) -> None:
        self.peers_map.setdefault(peers_node_address, state_hash)

    def put_in_conflict_map(self, peers_node_address: str, state_hash: _T) -> None:
        self.in_conflict_map.setdefault(peers_node_address, state_hash)

    @property
    def height(self) -> int:
        return self.my_state_hash.height

    @property
    def hash(self) -> bytes:
        return self.my_state_hash.hash

    def __str__(self) -> str:
        return (
            f"StateBlock{{\n"
            f"    myStateHash={self.my_state_hash},\n"
            f"    peersMap={self.peers_map},\n"
            f"    inConflictMap={self.in_conflict_map}\n"
            f"}}"
        )
