from typing import TYPE_CHECKING
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.trade.delayed_payout_address_provider import DelayedPayoutAddressProvider

if TYPE_CHECKING:
    from bisq.common.config.config import Config
    from bisq.core.dao.state.dao_state_service import DaoStateService


# TODO
class DaoFacade(DaoSetupService):

    def __init__(self, config: "Config", dao_state_service: "DaoStateService"):
        self.config = config
        self.dao_state_service = dao_state_service

    def get_param_value(self, param: Param, block_height: int = None) -> str:
        if block_height is None:
            block_height = self.dao_state_service.get_chain_height()

        return self.dao_state_service.get_param_value(param, block_height)

    def get_all_past_param_values(self, param: Param) -> set:
        _set = set[str]()
        return _set

    def get_all_donation_addresses(self):
        # We support any of the past addresses as well as in case the peer has not enabled the DAO or is out of sync we
        # do not want to break validation.
        all_past_param_values = self.get_all_past_param_values(
            Param.RECIPIENT_BTC_ADDRESS
        )

        # If Dao is deactivated we need to add the default address as getAllPastParamValues will not return us any.
        if not all_past_param_values:
            all_past_param_values.add(Param.RECIPIENT_BTC_ADDRESS.default_value)

        if self.config.base_currency_network.is_mainnet():
            # If Dao is deactivated we need to add the past addresses used as well.
            # This list need to be updated once a new address gets defined.
            all_past_param_values.add(DelayedPayoutAddressProvider.BM2019_ADDRESS)
            all_past_param_values.add(DelayedPayoutAddressProvider.BM2_ADDRESS)
            all_past_param_values.add(DelayedPayoutAddressProvider.BM3_ADDRESS)

        return all_past_param_values

    def is_dao_state_ready_and_in_sync(self) -> bool:
        raise RuntimeError(
            "DaoFacade.is_dao_state_ready_and_in_sync Not implemented yet"
        )
        
    def add_listeners(self):
        pass
    
    def start(self):
        pass

    def add_bsq_state_listener(self, listener: "DaoStateListener"):
        self.dao_state_service.add_dao_state_listener(listener)

    def remove_bsq_state_listener(self, listener: "DaoStateListener"):
        self.dao_state_service.remove_dao_state_listener(listener)

    @property
    def is_parse_block_chain_complete(self):
        return self.dao_state_service.parse_block_chain_complete