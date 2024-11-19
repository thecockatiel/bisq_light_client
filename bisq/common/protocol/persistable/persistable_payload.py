from abc import ABC
from bisq.common.payload import Payload

class PersistablePayload(Payload, ABC):
    """
    Interface for objects used inside Envelope or other Payloads.
    """
    
    def __hash__(self) -> int:
        return hash(self.to_proto_message().SerializeToString(deterministic=True))