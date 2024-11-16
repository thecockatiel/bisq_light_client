from abc import ABC
from bisq.core.common.payload import Payload

class PersistablePayload(Payload, ABC):
    """
    Interface for objects used inside Envelope or other Payloads.
    """
    pass