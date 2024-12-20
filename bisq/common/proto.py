from abc import ABC, abstractmethod
from google.protobuf.message import Message

class Proto(ABC):
    """
    Base interface for Envelope and Payload.
    """
    @abstractmethod
    def to_proto_message(self) -> Message:
        pass

    def serialize(self) -> bytes:
        return self.to_proto_message().SerializeToString()

    # If the class implements ExcludedFieldsProto this method will be overwritten so that
    # fields annotated with ExcludeForHash will be excluded.
    def serialize_for_hash(self) -> bytes:
        return self.to_proto_message().SerializeToString()
    
    def get_serialized_size(self):
        return self.to_proto_message().ByteSize()
    
    def __hash__(self) -> int:
        return hash(self.serialize_for_hash())