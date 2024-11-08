from abc import ABC, abstractmethod
from bisq.core.network.p2p.storage.payload.persistable_network_payload import (
    PersistableNetworkPayload,
)
from utils.clock import Clock


class DateTolerantPayload(PersistableNetworkPayload, ABC):
    """
    Interface for PersistableNetworkPayload which only get added if the date is inside a tolerance range.
    Used for AccountAgeWitness.
    """

    @abstractmethod
    def is_date_in_tolerance(self, clock: Clock) -> bool:
        pass
