from typing import TYPE_CHECKING
from bisq.core.dao.monitoring.model.state_block import StateBlock

if TYPE_CHECKING:
    from bisq.core.dao.monitoring.model.dao_state_hash import DaoStateHash


class DaoStateBlock(StateBlock["DaoStateHash"]):

    @property
    def is_self_created(self) -> bool:
        return self.my_state_hash.is_self_created
