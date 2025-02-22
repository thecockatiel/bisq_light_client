from abc import ABC
from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.common.util.utilities import bytes_as_hex_string


# shouldnt be instantiated directly
class StateHash(PersistablePayload, NetworkPayload, ABC):
    """
    Contains the blockHeight, the hash and the previous hash of the state.
    As the hash is created from the state at the particular height including the previous hash we get the history of
    the full chain included and we know if the hash matches at a particular height that all the past blocks need to match
    as well.
    """

    def __init__(self, height: int, hash: bytes):
        self.height = height
        self.hash = hash

    def has_equal_hash(self, other: "StateHash") -> bool:
        if not isinstance(other, StateHash):
            return False
        if self is other:
            return True
        return self.hash == other.hash

    def __str__(self) -> str:
        return (
            f"StateHash{{\n"
            f"     height={self.height},\n"
            f"     hash={bytes_as_hex_string(self.hash)}\n"
            f"}}"
        )

    def __eq__(self, other):
        if not isinstance(other, StateHash):
            return False
        return self.height == other.height and self.hash == other.hash

    def __hash__(self):
        return hash((self.height, self.hash))
