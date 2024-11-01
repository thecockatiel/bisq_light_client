from typing import TYPE_CHECKING
from bisq.core.common.payload import Payload
from bisq.core.common.protocol.persistable.persistable_payload import PersistablePayload
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    import proto.pb_pb2 as protobuf

class ProtoResolver(ABC):
    @abstractmethod
    def from_proto(self, proto: 'protobuf.PaymentAccountPayload' | 'protobuf.PersistableNetworkPayload') -> Payload:
        pass
