from typing import TYPE_CHECKING
from bisq.core.common.payload import Payload
from bisq.core.common.protocol.persistable.persistable_payload import PersistablePayload

if TYPE_CHECKING:
    import proto.pb_pb2 as protobuf



class ProtoResolver:
    def from_proto_payment_account(self, proto: 'protobuf.PaymentAccountPayload') -> Payload:
        # Convert PaymentAccountPayload to Payload
        pass

    def from_proto_persistable_network(self, proto: 'protobuf.PersistableNetworkPayload') -> PersistablePayload:
        # Convert PersistableNetworkPayload to PersistablePayload
        pass