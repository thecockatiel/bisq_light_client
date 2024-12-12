from typing import TYPE_CHECKING
from bisq.common.config.config import CONFIG, Config
from bisq.core.dao.governance.param.param import Param
from bisq.core.trade.delayed_payout_address_provider import DelayedPayoutAddressProvider

if TYPE_CHECKING:
    from bisq.core.dao.state.dao_state_service import DaoStateService

# TODO
class DaoFacade:
    
    def __init__(self, dao_state_service: "DaoStateService"):
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
        all_past_param_values = self.get_all_past_param_values(Param.RECIPIENT_BTC_ADDRESS)

        # If Dao is deactivated we need to add the default address as getAllPastParamValues will not return us any.
        if not all_past_param_values:
            all_past_param_values.add(Param.RECIPIENT_BTC_ADDRESS.default_value)

        if CONFIG.base_currency_network.is_mainnet():
            # If Dao is deactivated we need to add the past addresses used as well.
            # This list need to be updated once a new address gets defined.
            all_past_param_values.add(DelayedPayoutAddressProvider.BM2019_ADDRESS)
            all_past_param_values.add(DelayedPayoutAddressProvider.BM2_ADDRESS)
            all_past_param_values.add(DelayedPayoutAddressProvider.BM3_ADDRESS)

        return all_past_param_values
