from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.core.network.p2p.storage.payload.persistable_network_payload import PersistableNetworkPayload

class AppendOnlyDataStoreListener(Callable[["PersistableNetworkPayload"], None], ABC):
    @abstractmethod
    def on_added(self, payload: "PersistableNetworkPayload"):
        pass
    
    def __call__(self, payload: "PersistableNetworkPayload"):
        self.on_added(payload)