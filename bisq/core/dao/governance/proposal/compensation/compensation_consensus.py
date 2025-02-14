from typing import TYPE_CHECKING

from bisq.core.dao.governance.param.param import Param


if TYPE_CHECKING:
    from bisq.core.dao.state.dao_state_service import DaoStateService


class CompensationConsensus:

    @staticmethod
    def get_min_compensation_request_amount(
        dao_state_service: "DaoStateService", chain_height: int
    ):
        return dao_state_service.get_param_value_as_coin(
            Param.COMPENSATION_REQUEST_MIN_AMOUNT, chain_height
        )

    @staticmethod
    def get_max_compensation_request_amount(
        dao_state_service: "DaoStateService", chain_height: int
    ):
        return dao_state_service.get_param_value_as_coin(
            Param.COMPENSATION_REQUEST_MAX_AMOUNT, chain_height
        )
