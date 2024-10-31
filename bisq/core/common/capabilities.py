from dataclasses import dataclass
from typing import List, Set, Optional

from bisq.logging import get_logger
from .capability import Capability

logger = get_logger(__name__)

class Capabilities:
    """
    hold a set of capabilities and offers appropriate comparison methods.

    Author: Florian Reimair
    """

    # The global set of capabilities, i.e. the capabilities of the local app.
    app = None  # Will be initialized after the class definition

    # Defines which most recent capability any node need to support.
    # This helps to clean network from very old inactive but still running nodes.
    MANDATORY_CAPABILITY = Capability.DAO_STATE

    def __init__(self, capabilities: Optional[List[Capability]] = None):
        self.capabilities: frozenset[Capability] = frozenset(capabilities) if capabilities else frozenset()

    def set(self, capabilities: Optional[frozenset[Capability]] = None):
        self.capabilities = capabilities

    def add_all(self, capabilities: Optional[List[Capability]] = None):
        if capabilities:
            self.capabilities = self.capabilities.union(capabilities)

    def contains_all(self, required_items: Set[Capability]) -> bool:
        return self.capabilities.issuperset(required_items)

    def contains(self, capability: Capability) -> bool:
        return capability in self.capabilities

    def is_empty(self) -> bool:
        return not self.capabilities
    
    def __eq__(self, other):
        if type(other) is type(self):
            return self.capabilities.__eq__(other.capabilities)
        else:
            return False
    
    def __hash__(self):
        return self.capabilities.__hash__()

    @staticmethod
    def to_int_list(capabilities_obj: 'Capabilities') -> List[int]:
        return sorted([cap.value for cap in capabilities_obj.capabilities])

    @staticmethod
    def from_int_list(capabilities_list: List[int]) -> 'Capabilities':
        valid_capabilities = {
            cap for cap in Capability if 0 <= cap.value < len(Capability)
        }
        caps = {Capability(cap) for cap in capabilities_list if cap in valid_capabilities}
        return Capabilities(list(caps))

    @staticmethod
    def from_string_list(list_str: str) -> 'Capabilities':
        if not list_str:
            return Capabilities()
        entries = list_str.replace(" ", "").split(",")
        capabilities_list = []
        for c in entries:
            try:
                capabilities_list.append(int(c))
            except ValueError:
                continue
        return Capabilities.from_int_list(capabilities_list)

    def to_string_list(self) -> str:
        return ", ".join(map(str, self.to_int_list(self)))

    @staticmethod
    def has_mandatory_capability(capabilities_obj: 'Capabilities') -> bool:
        return Capabilities.has_mandatory_capability_specific(capabilities_obj, Capabilities.MANDATORY_CAPABILITY)

    @staticmethod
    def has_mandatory_capability_specific(capabilities_obj: 'Capabilities', mandatory_cap: Capability) -> bool:
        return any(c == mandatory_cap for c in capabilities_obj.capabilities)

    def __str__(self) -> str:
        return str(self.to_int_list(self))

    def pretty_print(self) -> str:
        return ", ".join([f"{cap.name} [{cap.value}]" for cap in sorted(self.capabilities, key=lambda x: x.value)])

    def size(self) -> int:
        return len(self.capabilities)

    def has_less(self, other: 'Capabilities') -> bool:
        return self.find_highest_capability() < other.find_highest_capability()

    def find_highest_capability(self) -> int:
        return sum(cap.value for cap in self.capabilities)

Capabilities.app = Capabilities()