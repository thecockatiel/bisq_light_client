from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.core.dao.state.model.governance.ballot import Ballot


class BallotListChangeListener(ABC):

    @abstractmethod
    def on_list_changed(self, changes: list["Ballot"]):
        pass
