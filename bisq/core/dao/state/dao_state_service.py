from typing import TYPE_CHECKING, Union
from bisq.core.dao.governance.param.param import Param
from bisq.core.util.coin.bsq_formatter import BsqFormatter
from utils.concurrency import ThreadSafeSet

if TYPE_CHECKING:
    from bisq.core.dao.state.dao_state_listener import DaoStateListener

# TODO: a dummy class for dao state handling for now

class DaoStateService():
    
    def __init__(self, bsq_formatter: BsqFormatter) -> None:
        self.dao_state_listeners: ThreadSafeSet["DaoStateListener"] = ThreadSafeSet()
        self.bsq_formatter = bsq_formatter
        
    def add_dao_state_listener(self, listener: "DaoStateListener") -> None:
        self.dao_state_listeners.add(listener)
    
    def remove_dao_state_listener(self, listener: "DaoStateListener") -> None:
        self.dao_state_listeners.discard(listener)
        
    def get_chain_height(self) -> int:
        return 0
    
    def get_param_value(self, param: Param, block_height: int):
        return param.default_value
    
    def get_param_value_as_coin(self, param: Param, block_height_or_param_value: Union[int, str]):
        if isinstance(block_height_or_param_value, int):
            block_height_or_param_value = self.get_param_value(param, block_height_or_param_value)
        return self.bsq_formatter.parse_param_value_to_coin(param, block_height_or_param_value)