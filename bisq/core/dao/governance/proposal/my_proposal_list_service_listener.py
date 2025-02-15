from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.core.dao.state.model.governance.proposal import Proposal


class MyProposalListServiceListener(ABC):

    @abstractmethod
    def on_list_changed(self, list: list["Proposal"]) -> None:
        pass
