
from dataclasses import dataclass
from typing import Set

from bisq.core.common.protocol.persistable.persistable_payload import PersistablePayload
import proto.pb_pb2 as protobuf

# moved from P2PDataStorage.ByteArray here

@dataclass(frozen=True)
class StorageByteArray(PersistablePayload):
    """
    Used as key object in map for cryptographic hash of stored data as byte[] as primitive data type cannot be used as key
    """
    
    # That object is saved to disc. We need to take care of changes to not break deserialization.
    _bytes: bytes
    
    def __post_init__(self):
        self.verify_bytes_not_empty()
    
    def verify_bytes_not_empty(self):
        if self._bytes is None:
            raise ValueError("Cannot create StorageByteArray(or P2PDataStorage.ByteArray) with None bytes argument.")
        if len(self._bytes) == 0:
            raise ValueError("Cannot create StorageByteArray(or P2PDataStorage.ByteArray) with empty bytes argument.")

    def __post_init__(self):
        if not self._bytes:
            raise ValueError("ByteArray cannot be empty")
        
    def __str__(self):
        return f"ByteArray{{bytes as Hex={self.get_hex()}}}"
    
    def __eq__(self, other):
        if not isinstance(other, StorageByteArray):
            return False
        return self._bytes == other._bytes
    
    def __hash__(self):
        return hash(self._bytes)

    def to_proto_message(self):
        return protobuf.ByteArray(bytes=self._bytes)

    @staticmethod
    def from_proto(proto: protobuf.ByteArray):
        return StorageByteArray(proto.bytes)

    def get_hex(self):
        return self._bytes.hex()

    @staticmethod
    def convert_bytes_set_to_bytearray_set(byte_set: Set[bytes]):
        return {StorageByteArray(b) for b in byte_set} if byte_set else set()
