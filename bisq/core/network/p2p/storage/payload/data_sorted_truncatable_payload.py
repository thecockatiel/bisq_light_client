from abc import ABC, abstractmethod
from datetime import datetime

from bisq.core.network.p2p.storage.payload.persistable_network_payload import PersistableNetworkPayload

class DateSortedTruncatablePayload(PersistableNetworkPayload, ABC):
    """
    Marker interface for PersistableNetworkPayloads which get truncated at initial data response in case we exceed
    the max items defined for that type of object. The truncation happens on a sorted list where we use the date for
    sorting so in case of truncation we prefer to receive the most recent data.
    """
    
    @abstractmethod
    def get_date(self) -> datetime:
        pass

    @abstractmethod
    def max_items(self) -> int:
        pass
