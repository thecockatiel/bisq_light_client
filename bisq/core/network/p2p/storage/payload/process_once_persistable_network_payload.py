from abc import ABC
from bisq.core.common.payload import Payload


class ProcessOncePersistableNetworkPayload(Payload, ABC):
    """
    Marker interface for PersistableNetworkPayloads that are only added during the FIRST call to
    P2PDataStorage::processDataResponse. This improves performance for objects that don't go out
    of sync frequently.
    """

    pass
