 
from abc import ABC

from bisq.core.common.payload import Payload
from .get_data_response_priority import GetDataResponsePriority

class NetworkPayload(Payload, ABC):
    """
    Interface for objects used inside WireEnvelope or other WirePayloads.
    """

    def get_get_data_response_priority(self) -> GetDataResponsePriority:
        return GetDataResponsePriority.LOW