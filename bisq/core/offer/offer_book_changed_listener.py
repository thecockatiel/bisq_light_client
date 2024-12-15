from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.core.offer.offer import Offer


class OfferBookChangedListener(ABC):
    @abstractmethod
    def on_added(self, offer: "Offer"):
        pass

    @abstractmethod
    def on_removed(self, offer: "Offer"):
        pass
