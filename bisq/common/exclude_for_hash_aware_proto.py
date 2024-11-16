from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from bisq.common.proto import Proto
if TYPE_CHECKING:
    import proto.pb_pb2 as protobuf
 
# NOTE: this only acts as a marker interface, it does not provide any functionality. it's up to the implementing class to provide the necessary functionality based on the original bisq code
# since this is only used in 2 classes, this is easy: Filter and DataAndSeqNrPair.
# in practice It's only Filter I think.
class ExcludeForHashAwareProto(Proto, ABC):
    @abstractmethod
    def to_proto(self, serialize_for_hash: bool = False) -> 'protobuf.StoragePayload':
        pass
