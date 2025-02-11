from abc import ABC, abstractmethod


class BondedAsset(ABC):
    """Represents the bonded asset (e.g. Role or Reputation)."""

    @property
    @abstractmethod
    def hash(self) -> bytes:
        pass

    @property
    @abstractmethod
    def uid(self) -> str:
        pass

    @property
    @abstractmethod
    def display_string(self) -> str:
        pass
