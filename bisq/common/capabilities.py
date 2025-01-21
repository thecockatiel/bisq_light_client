from typing import Iterable, Optional, Union

from bisq.common.capability import Capability
from bisq.common.setup.log_setup import get_logger

logger = get_logger(__name__)


class Capabilities:
    """
    hold a set of capabilities and offers appropriate comparison methods.

    Author: Florian Reimair
    """

    # The global set of capabilities, i.e. the capabilities of the local app.
    app: "Capabilities" = None  # Will be initialized after the class definition

    # Defines which most recent capability any node need to support.
    # This helps to clean network from very old inactive but still running nodes.
    MANDATORY_CAPABILITY = Capability.DAO_STATE

    def __init__(self, capabilities: Optional[Union[Iterable[Capability], "Capabilities"]] = None):
        if capabilities is None:
            self.capabilities = frozenset()
        elif isinstance(capabilities, Capabilities):
            self.capabilities = capabilities.capabilities
        else:
            self.capabilities = frozenset(capabilities)

    def set(self, capabilities: Optional[frozenset[Capability]] = None):
        self.capabilities = capabilities

    def add_all(self, capabilities: Optional[list[Capability]] = None):
        if capabilities:
            self.capabilities = self.capabilities.union(capabilities)

    def is_empty(self) -> bool:
        return len(self.capabilities) == 0

    def contains_all(self, required_items: Iterable[Capability]) -> bool:
        return self.capabilities.issuperset(required_items)

    def __contains__(self, capability):
        return capability in self.capabilities

    def __iter__(self):
        return iter(self.capabilities)

    def __eq__(self, other):
        if isinstance(other, Capabilities):
            return self.capabilities == other.capabilities
        else:
            return False

    def __len__(self):
        return len(self.capabilities)

    def __hash__(self):
        return None

    def __str__(self) -> str:
        return str(self.to_int_list(self))

    @staticmethod
    def to_int_list(capabilities_obj: "Capabilities") -> list[int]:
        return sorted([cap.value for cap in capabilities_obj.capabilities])

    @staticmethod
    def from_int_list(capabilities_list: list[int]) -> "Capabilities":
        caps = {
            Capability(cap) for cap in capabilities_list if 0 <= cap < len(Capability)
        }
        return Capabilities(caps)

    @staticmethod
    def from_string_list(list_str: str) -> "Capabilities":
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
    def has_mandatory_capability(
        capabilities: "Capabilities",
        mandatory_capability: Optional["Capability"] = None,
    ) -> bool:
        if mandatory_capability is None:
            mandatory_capability = Capabilities.MANDATORY_CAPABILITY
        return any(c == mandatory_capability for c in capabilities.capabilities)

    def pretty_print(self) -> str:
        return ", ".join(
            [
                f"{cap.name} [{cap.value}]"
                for cap in sorted(self.capabilities, key=lambda x: x.value)
            ]
        )

    # We return true if our capabilities have less capabilities than the parameter value
    def has_less(self, other: "Capabilities") -> bool:
        return self.find_highest_capability() < other.find_highest_capability()

    # We use the sum of all capabilities. Alternatively we could use the highest entry.
    # Neither would support removal of past capabilities, a use case we never had so far and which might have
    # backward compatibility issues, so we should treat capabilities as an append-only data structure.
    def find_highest_capability(self) -> int:
        return sum(cap.value for cap in self.capabilities)


Capabilities.app = Capabilities()
