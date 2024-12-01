
from abc import ABC, abstractmethod
from typing import List


class BridgeAddressProvider(ABC):
    @abstractmethod
    def get_bridge_addresses(self) -> List[str]:
        pass