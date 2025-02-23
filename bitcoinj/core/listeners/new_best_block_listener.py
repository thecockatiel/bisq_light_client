from abc import ABC, abstractmethod

from bitcoinj.core.block import Block


class NewBestBlockListener(ABC):
    """Listener interface for when a new block on the best chain is seen."""

    @abstractmethod
    def notify_new_best_block(self, block: "Block"):
        pass
