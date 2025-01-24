from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from google.protobuf.message import Message
from bisq.common.proto import Proto
if TYPE_CHECKING:
    import pb_pb2 as protobuf
 
# NOTE: this only acts as a marker interface, it does not provide any functionality. it's up to the implementing class to provide the necessary functionality based on the original bisq code
# since this is only used in 2 classes, this is easy: Filter and DataAndSeqNrPair.
# in practice It's only Filter I think.
class ExcludeForHashAwareProto(Proto, ABC):
    @abstractmethod
    def to_proto(self, serialize_for_hash: bool = False) -> 'protobuf.StoragePayload':
        pass
    
    def to_proto_message(self):
        return self.complete_proto()

    def serialize(self):
        return self.to_proto(False).SerializeToString()
    
    def serialize_for_hash(self):
        return self.to_proto(True).SerializeToString()

    def complete_proto(self):
        return self.to_proto(False)
    
    def get_serialized_size(self):
        return self.to_proto(False).ByteSize()