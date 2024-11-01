
from abc import ABC, abstractmethod
from typing import Collection, TYPE_CHECKING

if TYPE_CHECKING:
    from ..node_address import NodeAddress

class SeedNodeRepository(ABC):
    
    @abstractmethod
    def is_seed_node(self, node_address: 'NodeAddress') -> bool:
        pass
    
    @abstractmethod
    def get_seed_node_addresses(self) -> Collection['NodeAddress']:
        pass