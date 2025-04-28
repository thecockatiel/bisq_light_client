from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING
from bisq.common.config.config import Config
from bisq.core.dao.governance.param.param import Param
from bitcoinj.base.coin import Coin
from utils.data import SimpleProperty
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.dao.state.dao_state_service import DaoStateService


class FeeService:
    # Miner fees are between 1-600 sat/vbyte. We try to stay on the safe side. BTC_DEFAULT_TX_FEE is only used if our
    # fee service would not deliver data.
    BTC_DEFAULT_TX_FEE = 50
    filter_manager: "FilterManager" = None
    dao_state_service: "DaoStateService" = None

    def __init__(self, dao_state_service: "DaoStateService"):
        self.logger = get_ctx_logger(__name__)
        FeeService.dao_state_service = dao_state_service
        self.fee_update_counter_property = SimpleProperty(0)
        self.tx_fee_per_vbyte = FeeService.BTC_DEFAULT_TX_FEE
        self.last_request = 0
        self.min_fee_per_vbyte = 0

    def on_all_services_initialized(self, provided_filter_manager: "FilterManager"):
        FeeService.filter_manager = provided_filter_manager
        self.min_fee_per_vbyte = Config.BASE_CURRENCY_NETWORK_VALUE.get_default_min_fee_per_vbyte()

    @staticmethod
    def get_fee_from_param_as_coin(param: Param) -> Coin:
        # if specified, filter values take precedence
        from_filter = FeeService.get_filter_from_param_as_coin(param)
        if from_filter > Coin.ZERO():
            return from_filter
        return (FeeService.dao_state_service.get_param_value_as_coin(param, FeeService.dao_state_service.chain_height) 
                if FeeService.dao_state_service is not None 
                else Coin.ZERO())

    @staticmethod
    def get_filter_from_param_as_coin(param: Param) -> Coin:
        filter_val = Coin.ZERO()
        if FeeService.filter_manager is not None and FeeService.filter_manager.get_filter() is not None:
            filter = FeeService.filter_manager.get_filter()
            if param == Param.DEFAULT_MAKER_FEE_BTC:
                filter_val = Coin.value_of(filter.maker_fee_btc)
            elif param == Param.DEFAULT_TAKER_FEE_BTC:
                filter_val = Coin.value_of(filter.taker_fee_btc)
            elif param == Param.DEFAULT_MAKER_FEE_BSQ:
                filter_val = Coin.value_of(filter.maker_fee_bsq)
            elif param == Param.DEFAULT_TAKER_FEE_BSQ:
                filter_val = Coin.value_of(filter.taker_fee_bsq)
        return filter_val

    @staticmethod
    def get_maker_fee_per_btc(currency_for_fee_is_btc: bool) -> Coin:
        return (FeeService.get_fee_from_param_as_coin(Param.DEFAULT_MAKER_FEE_BTC) 
                if currency_for_fee_is_btc 
                else FeeService.get_fee_from_param_as_coin(Param.DEFAULT_MAKER_FEE_BSQ))

    @staticmethod
    def get_min_maker_fee(currency_for_fee_is_btc: bool) -> Coin:
        return (FeeService.get_fee_from_param_as_coin(Param.MIN_MAKER_FEE_BTC) 
                if currency_for_fee_is_btc 
                else FeeService.get_fee_from_param_as_coin(Param.MIN_MAKER_FEE_BSQ))

    @staticmethod
    def get_taker_fee_per_btc(currency_for_fee_is_btc: bool) -> Coin:
        return (FeeService.get_fee_from_param_as_coin(Param.DEFAULT_TAKER_FEE_BTC) 
                if currency_for_fee_is_btc 
                else FeeService.get_fee_from_param_as_coin(Param.DEFAULT_TAKER_FEE_BSQ))

    @staticmethod
    def get_min_taker_fee(currency_for_fee_is_btc: bool) -> Coin:
        return (FeeService.get_fee_from_param_as_coin(Param.MIN_TAKER_FEE_BTC) 
                if currency_for_fee_is_btc 
                else FeeService.get_fee_from_param_as_coin(Param.MIN_TAKER_FEE_BSQ))

    def get_tx_fee(self, vsize_in_vbytes: int) -> Coin:
        return self.get_tx_fee_per_vbyte().multiply(vsize_in_vbytes)

    def get_tx_fee_per_vbyte(self) -> Coin:
        return Coin.value_of(self.tx_fee_per_vbyte)

    def is_fee_available(self) -> bool:
        return self.fee_update_counter_property.get() > 0

    def update_fee_info(self, tx_fee_per_vbyte: int, min_fee_per_vbyte: int) -> None:
        self.tx_fee_per_vbyte = tx_fee_per_vbyte
        self.min_fee_per_vbyte = min_fee_per_vbyte
        self.fee_update_counter_property.set(self.fee_update_counter_property.get() + 1)
        self.last_request = get_time_ms()
        self.logger.info(f"BTC tx fee: txFeePerVbyte={tx_fee_per_vbyte} minFeePerVbyte={min_fee_per_vbyte}")

