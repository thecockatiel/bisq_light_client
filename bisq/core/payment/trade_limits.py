from typing import TYPE_CHECKING, Optional
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.state.dao_state_listener import DaoStateListener
import threading


if TYPE_CHECKING:
    from bitcoinj.base.coin import Coin
    from bisq.core.dao.state.dao_state_service import DaoStateService
    

class TradeLimits(DaoStateListener):
    INSTANCE: Optional["TradeLimits"] = None
    _cached_max_trade_limit: Optional["Coin"] = None  # Note: volatile equivalent in Python
    _lock = threading.Lock()
    
    def __init__(self, dao_state_service: "DaoStateService") -> None:
        self.dao_state_service = dao_state_service
        TradeLimits.INSTANCE = self
        
    def on_all_services_initialized(self):
        pass # does nothing

    def on_parse_block_complete_after_batch_processing(self, block):
        with self._lock:
            self._cached_max_trade_limit = None

    def get_max_trade_limit_from_dao_param(self) -> "Coin":
        """
        The default trade limits defined as statics in PaymentMethod are only used until the DAO
        is fully synchronized. NOTE: TODO: python implementation does not sync DAO yet.

        See: bisq.core.payment.payload.PaymentMethod
        Returns:
            Coin: the maximum trade limit set by the DAO.
        """
        with self._lock:
            limit = self._cached_max_trade_limit
            if limit is None:
                self._cached_max_trade_limit = limit = self.dao_state_service.get_param_value_as_coin(Param.MAX_TRADE_LIMIT, self.dao_state_service.get_chain_height())
        return limit

    # We possibly rounded value for the first month gets multiplied by 4 to get the trade limit after the account
    # age witness is not considered anymore (> 2 months).
    
    def get_rounded_risk_based_trade_limit(self, max_limit: int, risk_factor: int) -> int:
        """
        Args:
            max_limit (int): Satoshi value of max trade limit
            risk_factor (int): Risk factor to decrease trade limit for higher risk payment methods

        Returns:
            int: Possibly adjusted trade limit to avoid that in first month trade limit get precision < 4
        """
        return self.get_first_month_risk_based_trade_limit(max_limit, risk_factor) * 4

    # The first month we allow only 0.25% of the trade limit. We want to ensure that precision is <=4 otherwise we round.

    def get_first_month_risk_based_trade_limit(self, max_limit: int, risk_factor: int) -> int:
        """
        Args:
            max_limit (int): Satoshi value of max trade limit
            risk_factor (int): Risk factor to decrease trade limit for higher risk payment methods

        Returns:
            int: Rounded trade limit for first month to avoid BTC value with precision < 4
        """
        # The first month we use 1/4 of the max limit. We multiply with riskFactor, so 1/ (4 * 8) is smallest limit in
        # first month of a maxTradeLimitHighRisk method
        smallest_limit = max_limit // (4 * risk_factor) # e.g. 100000000 / 32 = 3125000
        # We want to avoid more than 4 decimal places (100000000 / 32 = 3125000 or 1 BTC / 32 = 0.03125 BTC).
        # We want rounding to 0.0313 BTC
        return ((smallest_limit + 5000) // 10000) * 10000

