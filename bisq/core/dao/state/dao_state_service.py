from typing import TYPE_CHECKING, Union
from bisq.core.dao.governance.param.param import Param
from utils.concurrency import ThreadSafeSet
from bisq.core.dao.dao_setup_service import DaoSetupService

if TYPE_CHECKING:
    from bisq.core.util.coin.bsq_formatter import BsqFormatter
    from proto.pb_pb2 import DaoState
    from bisq.core.dao.state.genesis_tx_info import GenesisTxInfo
    from bisq.core.dao.state.dao_state_listener import DaoStateListener

# TODO: a dummy class for dao state handling for now


class DaoStateService(DaoSetupService):

    def __init__(
        self,
        dao_state: "DaoState",
        genesis_tx_info: "GenesisTxInfo",
        bsq_formatter: "BsqFormatter",
    ) -> None:
        self.dao_state_listeners: ThreadSafeSet["DaoStateListener"] = ThreadSafeSet()
        self.dao_state = dao_state
        self.genesis_tx_info = genesis_tx_info
        self.bsq_formatter = bsq_formatter
        self.parse_block_chain_complete = False
        self.allow_dao_state_change = False

    def add_listeners(self):
        pass

    def start(self):
        self.allow_dao_state_change = True
        self.assert_dao_state_change()
        self.dao_state.chain_height = self.genesis_tx_info.genesis_block_height

    def add_dao_state_listener(self, listener: "DaoStateListener") -> None:
        self.dao_state_listeners.add(listener)

    def remove_dao_state_listener(self, listener: "DaoStateListener") -> None:
        self.dao_state_listeners.discard(listener)

    def get_chain_height(self) -> int:
        return self.dao_state.chain_height

    def get_param_value(self, param: Param, block_height: int):
        return param.default_value

    def get_param_value_as_coin(
        self, param: Param, block_height_or_param_value: Union[int, str]
    ):
        if isinstance(block_height_or_param_value, int):
            block_height_or_param_value = self.get_param_value(
                param, block_height_or_param_value
            )
        return self.bsq_formatter.parse_param_value_to_coin(
            param, block_height_or_param_value
        )

    def get_genesis_block_height(self) -> int:
        return self.genesis_tx_info.genesis_block_height

    def assert_dao_state_change(self):
        if not self.allow_dao_state_change:
            raise RuntimeError(
                "We got a call which would change the daoState outside of the allowed event phase"
            )
    
    def get_last_block(self):
        return None
