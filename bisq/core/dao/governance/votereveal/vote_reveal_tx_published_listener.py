from abc import ABC, abstractmethod
from collections.abc import Callable


class VoteRevealTxPublishedListener(Callable[[str], None], ABC):

    @abstractmethod
    def on_vote_reveal_tx_published(self, tx_id: str):
        pass

    def __call__(self, tx_id: str):
        self.on_vote_reveal_tx_published(tx_id)
