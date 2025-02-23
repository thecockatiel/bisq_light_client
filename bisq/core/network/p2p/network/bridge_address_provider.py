
from abc import ABC, abstractmethod


class BridgeAddressProvider(ABC):
    @abstractmethod
    def get_bridge_addresses(self) -> list[str]:
        pass