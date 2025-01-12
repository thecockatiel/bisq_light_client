from typing import TYPE_CHECKING
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload

if TYPE_CHECKING:
    from bisq.core.dao.state.model.governance.param_change import ParamChange


# TODO
class DaoState:
    """
    Root class for mutable state of the DAO.
    Holds both blockchain data as well as data derived from the governance process (voting).

    One BSQ block with empty txs adds 152 bytes which results in about 8 MB/year

    For supporting the hashChain we need to ensure deterministic sorting behaviour of all collections so we use a
    TreeMap which is sorted by the key.
    """

    def __init__(self, chain_height: int = 0):
        super().__init__()
        # Is set initially to genesis height
        self.chain_height = chain_height
        self.param_change_list: list["ParamChange"] = []
