from typing import TYPE_CHECKING
from bisq.common.config.config import Config
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.wallet.restrictions import Restrictions
from bisq.core.dao.governance.consensus_critical import ConsensusCritical

from bisq.core.dao.governance.param.param_type import ParamType
from bisq.core.dao.governance.proposal.param.param_validation_exception import (
    ParamValidationException,
)
from bisq.core.dao.governance.proposal.proposal_validation_exception import (
    ProposalValidationException,
)
from bisq.core.dao.governance.proposal.proposal_validator import ProposalValidator
from bisq.core.dao.state.model.governance.change_param_proposal import (
    ChangeParamProposal,
)
from bisq.core.locale.res import Res
from bisq.core.util.validation.btc_address_validator import BtcAddressValidator
from bitcoinj.base.coin import Coin
from utils.preconditions import check_argument
from bisq.core.dao.governance.param.param import Param

if TYPE_CHECKING:
    from bisq.core.util.coin.bsq_formatter import BsqFormatter
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.model.governance.proposal import Proposal

logger = get_logger(__name__)


class ChangeParamValidator(ProposalValidator, ConsensusCritical):
    """
    Changes here can potentially break consensus!

    We do not store the values as the actual data type (Coin, int, String) but as Strings. So we need to convert it to the
    expected data type even if we get the data not from user input.
    """

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        period_service: "PeriodService",
        bsq_formatter: "BsqFormatter",
    ):
        super().__init__(dao_state_service, period_service)
        self.bsq_formatter = bsq_formatter

    def validate_data_fields(self, proposal: "Proposal") -> None:
        try:
            super().validate_data_fields(proposal)

            # Only once parsing is complete we can check for param changes
            if self.dao_state_service.parse_block_chain_complete:
                if not isinstance(proposal, ChangeParamProposal):
                    raise ProposalValidationException(
                        "Proposal must be of type ChangeParamProposal"
                    )
                self._validate_param_value_at_height(
                    proposal.param,
                    proposal.param_value,
                    self.get_block_height(proposal),
                )
                check_argument(
                    len(proposal.param_value) <= 200,
                    "ParamValue must not exceed 200 chars",
                )
        except ProposalValidationException as e:
            raise e
        except Exception as throwable:
            raise ProposalValidationException(throwable) from throwable

    def validate_param_value(self, param: "Param", input_value: str) -> None:
        block_height = self.period_service.chain_height
        self._validate_param_value_at_height(param, input_value, block_height)

    def _validate_param_value_at_height(
        self, param: "Param", input_value: str, block_height: int
    ) -> None:
        current_param_value = self.dao_state_service.get_param_value(
            param, block_height
        )
        self._validate_param_value(param, current_param_value, input_value)

    def _validate_param_value(
        self, param: "Param", current_param_value: str, input_value: str
    ) -> None:
        try:
            if param.param_type == ParamType.UNDEFINED:
                pass
            elif param.param_type == ParamType.BSQ:
                current_param_value_as_coin = (
                    self.dao_state_service.get_param_value_as_coin(
                        param, current_param_value
                    )
                )
                input_value_as_coin = self.dao_state_service.get_param_value_as_coin(
                    param, input_value
                )
                self._validate_bsq_value(
                    current_param_value_as_coin, input_value_as_coin, param
                )
            elif param.param_type == ParamType.BTC:
                current_param_value_as_coin = (
                    self.dao_state_service.get_param_value_as_coin(
                        param, current_param_value
                    )
                )
                input_value_as_coin = self.dao_state_service.get_param_value_as_coin(
                    param, input_value
                )
                self._validate_btc_value(
                    current_param_value_as_coin, input_value_as_coin, param
                )
            elif param.param_type == ParamType.PERCENT:
                current_param_value_as_percent = (
                    self.dao_state_service.get_param_value_as_percent_double(
                        current_param_value
                    )
                )
                input_value_as_percent = (
                    self.dao_state_service.get_param_value_as_percent_double(
                        input_value
                    )
                )
                self._validate_percent_value(
                    current_param_value_as_percent, input_value_as_percent, param
                )
            elif param.param_type == ParamType.BLOCK:
                current_param_value_as_block = (
                    self.dao_state_service.get_param_value_as_block(current_param_value)
                )
                input_value_as_block = self.dao_state_service.get_param_value_as_block(
                    input_value
                )
                self._validate_block_value(
                    current_param_value_as_block, input_value_as_block, param
                )
            elif param.param_type == ParamType.ADDRESS:
                self._validate_address_value(current_param_value, input_value)
            else:
                logger.warning(
                    "Param type {} not handled in switch case at validate_param_value",
                    param.param_type,
                )
        except ParamValidationException as e:
            raise e
        except ValueError as t:
            raise ParamValidationException(
                Res.get("validation.numberFormatException", str(t).lower())
            ) from t
        except Exception as t:
            raise ParamValidationException(t) from t

    def _validate_bsq_value(
        self,
        current_param_value_as_coin: Coin,
        input_value_as_coin: Coin,
        param: "Param",
    ) -> None:
        if param in [
            Param.DEFAULT_MAKER_FEE_BSQ,
            Param.DEFAULT_TAKER_FEE_BSQ,
            Param.MIN_MAKER_FEE_BSQ,
            Param.MIN_TAKER_FEE_BSQ,
        ]:
            pass
        elif param in [Param.PROPOSAL_FEE, Param.BLIND_VOTE_FEE]:
            pass
        elif param in [
            Param.COMPENSATION_REQUEST_MIN_AMOUNT,
            Param.REIMBURSEMENT_MIN_AMOUNT,
            Param.COMPENSATION_REQUEST_MAX_AMOUNT,
            Param.REIMBURSEMENT_MAX_AMOUNT,
        ]:
            check_argument(
                input_value_as_coin.value
                >= Restrictions.get_min_non_dust_output().value,
                Res.get(
                    "validation.amountBelowDust",
                    Restrictions.get_min_non_dust_output().value,
                ),
            )
            check_argument(
                input_value_as_coin.value <= 200000000,
                Res.get("validation.inputTooLarge", "200 000 BSQ"),
            )
        elif param in [
            Param.QUORUM_COMP_REQUEST,
            Param.QUORUM_REIMBURSEMENT,
            Param.QUORUM_CHANGE_PARAM,
            Param.QUORUM_ROLE,
            Param.QUORUM_CONFISCATION,
            Param.QUORUM_GENERIC,
            Param.QUORUM_REMOVE_ASSET,
        ]:
            check_argument(
                input_value_as_coin.value > 100000,
                Res.get("validation.inputTooSmall", "1000 BSQ"),
            )
        elif param == Param.ASSET_LISTING_FEE_PER_DAY:
            pass
        elif param == Param.BONDED_ROLE_FACTOR:
            check_argument(
                input_value_as_coin.value > 100,
                Res.get("validation.inputTooSmall", "1 BSQ"),
            )

        check_argument(
            input_value_as_coin.is_positive(),
            Res.get("validation.inputTooSmall", "0 BSQ"),
        )
        self._validation_change(
            float(current_param_value_as_coin.value),
            float(input_value_as_coin.value),
            param,
        )

    def _validate_btc_value(
        self,
        current_param_value_as_coin: Coin,
        input_value_as_coin: Coin,
        param: "Param",
    ) -> None:
        if param in [
            Param.DEFAULT_MAKER_FEE_BTC,
            Param.DEFAULT_TAKER_FEE_BTC,
            Param.MIN_MAKER_FEE_BTC,
            Param.MIN_TAKER_FEE_BTC,
        ]:
            check_argument(
                input_value_as_coin.value
                >= Restrictions.get_min_non_dust_output().value,
                Res.get(
                    "validation.amountBelowDust",
                    Restrictions.get_min_non_dust_output().value,
                ),
            )
        elif param in [Param.ASSET_MIN_VOLUME, Param.MAX_TRADE_LIMIT]:
            check_argument(
                input_value_as_coin.is_positive(),
                Res.get("validation.inputTooSmall", "0"),
            )

        self._validation_change(
            float(current_param_value_as_coin.value),
            float(input_value_as_coin.value),
            param,
        )

    def _validate_percent_value(
        self,
        current_param_value_as_percent: float,
        input_value_as_percent: float,
        param: "Param",
    ) -> None:
        if param in [
            Param.THRESHOLD_COMP_REQUEST,
            Param.THRESHOLD_REIMBURSEMENT,
            Param.THRESHOLD_CHANGE_PARAM,
            Param.THRESHOLD_ROLE,
            Param.THRESHOLD_CONFISCATION,
            Param.THRESHOLD_GENERIC,
            Param.THRESHOLD_REMOVE_ASSET,
        ]:
            # We show only 2 decimals in the UI for % value
            check_argument(
                input_value_as_percent >= 0.5001,
                Res.get("validation.inputTooSmall", "50%"),
            )
            check_argument(
                input_value_as_percent <= 1,
                Res.get("validation.inputTooLarge", "100%"),
            )
        elif param == Param.ARBITRATOR_FEE:
            check_argument(
                input_value_as_percent >= 0, Res.get("validation.mustNotBeNegative")
            )

        self._validation_change(
            current_param_value_as_percent, input_value_as_percent, param
        )

    def _validate_block_value(
        self,
        current_param_value_as_block: int,
        input_value_as_block: int,
        param: "Param",
    ) -> None:
        is_mainnet = Config.BASE_CURRENCY_NETWORK_VALUE.is_mainnet()
        if param == [Param.LOCK_TIME_TRADE_PAYOUT, Param.PHASE_UNDEFINED]:
            pass
        elif param in [
            Param.PHASE_PROPOSAL,
            Param.PHASE_BREAK1,
            Param.PHASE_BLIND_VOTE,
            Param.PHASE_BREAK2,
            Param.PHASE_VOTE_REVEAL,
            Param.PHASE_BREAK3,
        ]:
            if is_mainnet:
                check_argument(
                    input_value_as_block >= 6,
                    Res.get("validation.inputToBeAtLeast", "6 blocks"),
                )
        elif param == Param.PHASE_RESULT:
            if is_mainnet:
                check_argument(
                    input_value_as_block >= 1,
                    Res.get("validation.inputToBeAtLeast", "1 block"),
                )

        self._validation_change(
            float(current_param_value_as_block), float(input_value_as_block), param
        )
        # We allow 0 values (e.g. time lock for trade)
        check_argument(
            input_value_as_block >= 0, Res.get("validation.mustNotBeNegative")
        )

    def _validate_address_value(
        self, current_param_value: str, input_value: str
    ) -> None:
        check_argument(
            input_value != current_param_value, Res.get("validation.mustBeDifferent")
        )
        validation_result = BtcAddressValidator().validate_btc_address(input_value)
        if not validation_result.is_valid:
            raise ParamValidationException(validation_result.error_message)

    def _validation_change(
        self, current_param_value: float, input_value: float, param: "Param"
    ) -> None:
        self.validate_change(
            current_param_value,
            input_value,
            param.max_decrease,
            param.max_increase,
            param,
        )

    def validate_change(
        self,
        current_value: float,
        new_value: float,
        min: float,
        max: float,
        param: "Param",
    ) -> None:
        """
        Args:
            current_value (float): The current value of the parameter.
            new_value (float): The new value of the parameter.
            min (float): Decrease of param value limited to current value / maxDecrease. If 0 we don't apply the check and any change is possible
            max (float): Increase of param value limited to current value * maxIncrease. If 0 we don't apply the check and any change is possible
            param (Param): The parameter being validated.

        Raises:
            ParamValidationException: If the validation fails due to any of the following reasons:
                - The new value is the same as the current value.
                - The current value is 0 and the parameter cannot be changed.
                - The new value exceeds the maximum allowed change ratio.
                - The new value is below the minimum allowed change ratio.
        """
        # No need for translation as it would be a developer error to use such min/max values
        check_argument(min >= 0, "Min must be >= 0")
        check_argument(max >= 0, "Max must be >= 0")
        if current_value == new_value:
            raise ParamValidationException(
                "Validation must be different",
                ParamValidationException.ERROR.SAME,
            )

        if max == 0:
            return

        # JAVA TODO some cases with min = 0 and max not 0 or the other way round are not correctly implemented yet.
        #  Not intended to be used that way anyway but should be fixed...
        change = new_value / current_value if current_value != 0 else 0
        if change > max:
            val = current_value * max
            value = self._get_formatted_value(param, val)
            raise ParamValidationException(
                Res.get("validation.inputTooLarge", value),
                ParamValidationException.ERROR.TOO_HIGH,
            )

        if min == 0:
            return

        # If min/max are > 0 and currentValue is 0 it cannot be changed. min/max must be 0 in such cases.
        if current_value == 0:
            raise ParamValidationException(
                Res.get("validation.cannotBeChanged"),
                ParamValidationException.ERROR.NO_CHANGE_POSSIBLE,
            )

        if change < (1 / min):
            val = current_value / min
            value = self._get_formatted_value(param, val)
            raise ParamValidationException(
                Res.get("validation.inputToBeAtLeast", value),
                ParamValidationException.ERROR.TOO_LOW,
            )

    def _get_formatted_value(self, param: "Param", val: float) -> str:
        value = str(val)
        if param.param_type == ParamType.UNDEFINED:
            pass  # Not used
        elif param.param_type == ParamType.BSQ:
            value = self.bsq_formatter.format_bsq_satoshis(int(val))
        elif param.param_type == ParamType.BTC:
            value = self.bsq_formatter.format_btc_satoshis(int(val))
        elif param.param_type == ParamType.PERCENT:
            value = str(val * 100)
        elif param.param_type == ParamType.BLOCK:
            value = str(round(val))
        elif param.param_type == ParamType.ADDRESS:
            pass  # Not used here
        return self.bsq_formatter.format_param_value(param, value)
