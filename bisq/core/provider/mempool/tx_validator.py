import json
from typing import TYPE_CHECKING, Any, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.core.dao.governance.param.param import Param
from bitcoinj.base.coin import Coin
from bisq.core.provider.mempool.fee_validation_status import FeeValidationStatus


if TYPE_CHECKING:
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.filter.filter_manager import FilterManager

logger = get_logger(__name__)

class TxValidator:
    FEE_TOLERANCE = 0.5  # we expect fees to be at least 50% of target
    BLOCK_TOLERANCE = 599999  # allow really old offers with weird fee addresses

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        tx_id: str,
        filter_manager: "FilterManager",
        amount: Optional[Coin] = None,
        is_fee_currency_btc: Optional[bool] = None,
        fee_payment_block_height: int = None,
    ):
        self.dao_state_service = dao_state_service
        self.tx_id = tx_id
        self.amount = amount
        self.is_fee_currency_btc = is_fee_currency_btc
        self.fee_payment_block_height = (
            fee_payment_block_height or 0
        )  # applicable to maker and taker fees
        self.chain_height = dao_state_service.chain_height
        self.filter_manager = filter_manager
        self.json_txt = ""
        self.status = FeeValidationStatus.NOT_CHECKED_YET

    def get_result(self):
        return self.status.passes
    
    def end_result(self, status: FeeValidationStatus, title: str = None) -> "TxValidator":
        if title is None:
            title = status.name
        self.status = status
        if self.status.passes:
            logger.info(f"{title} : {self.status.name}")
        else:
            logger.warning(f"{title} : {self.status.name}")
        return self

    def __str__(self):
        return self.status.name

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def parse_json_validate_maker_fee_tx(self, json_txt: str, btc_fee_receivers: list[str]) -> "TxValidator":
        self.json_txt = json_txt
        try:
            status = self._initial_sanity_checks(self.tx_id, json_txt)
            if status.passes:
                status = self._check_fee_address_btc(json_txt, btc_fee_receivers)
                if status.passes:
                    status = self._check_fee_amount_btc(
                        json_txt, 
                        self.amount, 
                        True, 
                        self._get_block_height_for_fee_calculation(json_txt)
                    )
        except json.JSONDecodeError as e:
            logger.info(f"The maker fee tx JSON validation failed with reason: {str(e)}")
            status = FeeValidationStatus.NACK_JSON_ERROR
        
        return self.end_result(status, "Maker tx validation (BTC)")

    def validate_bsq_fee_tx(self, is_maker: bool) -> "TxValidator":
        # TODO: dai_state_service needs to be implemented first
        raise NotImplementedError("DAO state service not implemented yet")
        # tx = self.dao_state_service.get_tx(self.tx_id)
        # status_str = f"{'Maker' if is_maker else 'Taker'} tx validation (BSQ)"
        
        # if tx is None:
        #     tx_age = self.chain_height - self.fee_payment_block_height
        #     if tx_age > 48:
        #         # still unconfirmed after 8 hours grace period we assume there may be SPV wallet issue.
        #         # see github.com/bisq-network/bisq/issues/6603
        #         status_str = f"BSQ tx {self.tx_id} not found, age={tx_age}: FAIL."
        #         return self.end_result(FeeValidationStatus.NACK_BSQ_FEE_NOT_FOUND, status_str)
        #     else:
        #         logger.info(f"DAO does not yet have the tx {self.tx_id} (age={tx_age}), bypassing check of burnt BSQ amount.")
        #         return self.end_result(FeeValidationStatus.ACK_BSQ_TX_IS_NEW, status_str)
        # else:
        #     return self.end_result(
        #         self._check_fee_amount_bsq(tx, self.amount, is_maker, self.fee_payment_block_height),
        #         status_str, 
        #     )

    def parse_json_validate_taker_fee_tx(self, json_txt: str, btc_fee_receivers: list[str]) -> "TxValidator":
        self.json_txt = json_txt
        try:
            status = self._initial_sanity_checks(self.tx_id, json_txt)
            if status.passes:
                status = self._check_fee_address_btc(json_txt, btc_fee_receivers)
                if status.passes:
                    status = self._check_fee_amount_btc(
                        json_txt, 
                        self.amount, 
                        False, 
                        self._get_block_height_for_fee_calculation(json_txt)
                    )
        except json.JSONDecodeError as e:
            logger.info(f"The taker fee tx JSON validation failed with reason: {str(e)}")
            status = FeeValidationStatus.NACK_JSON_ERROR
        
        return self.end_result(status, "Taker tx validation (BTC)")

    def parse_json_validate_tx(self) -> int:
        try:
            if not self._initial_sanity_checks(self.tx_id, self.json_txt).passes:
                return -1
            return self._get_tx_confirms(self.json_txt, self.chain_height)
        except json.JSONDecodeError:
            return -1

    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def _check_fee_address_btc(self, json_txt: str, btc_fee_receivers: list[str]) -> FeeValidationStatus:
        try:
            _, json_vout = self._get_vin_and_vout(json_txt)
            json_vout0 = json_vout[0]
            fee_address = json_vout0.get("scriptpubkey_address")
            logger.debug(f"fee address: {fee_address}")
            
            if fee_address in btc_fee_receivers:
                return FeeValidationStatus.ACK_FEE_OK
            elif self._get_block_height_for_fee_calculation(json_txt) < TxValidator.BLOCK_TOLERANCE:
                logger.info(f"Leniency rule, unrecognised fee receiver but its a really old offer so let it pass, {fee_address}")
                return FeeValidationStatus.ACK_FEE_OK
            else:
                error = f"fee address: {fee_address} was not a known BTC fee receiver"
                logger.info(error)
                logger.info(f"Known BTC fee receivers: {btc_fee_receivers}")
                return FeeValidationStatus.NACK_UNKNOWN_FEE_RECEIVER
        except Exception as e:
            logger.warning(str(e))
            return FeeValidationStatus.NACK_JSON_ERROR

    def _check_fee_amount_btc(self, json_txt: str, trade_amount: Coin, is_maker: bool, block_height: int) -> FeeValidationStatus:
        json_vin, json_vout = self._get_vin_and_vout(json_txt)
        json_vin0 = json_vin[0]
        json_vout0 = json_vout[0]

        json_vin0_prevout: dict = json_vin0.get("prevout", None)
        if not json_vin0_prevout:
            raise json.JSONDecodeError("vin[0].prevout missing", json_txt, 0)

        vin0_value = json_vin0_prevout.get("value", None)
        fee_value = json_vout0.get("value", None)
        if vin0_value is None or fee_value is None:
            raise json.JSONDecodeError("vin/vout missing data", json_txt, 0)
        
        fee_value = int(fee_value)
        logger.debug(f"BTC fee: {fee_value}")

        min_fee_param = Param.MIN_MAKER_FEE_BTC if is_maker else Param.MIN_TAKER_FEE_BTC
        expected_fee = self._calculate_fee(
            trade_amount,
            self._get_maker_fee_rate_btc(block_height) if is_maker else self._get_taker_fee_rate_btc(block_height),
            min_fee_param
        )

        fee_value_as_coin = Coin.value_of(fee_value)
        expected_fee_as_long = expected_fee.value
        description = f"Expected BTC fee: {expected_fee} sats, actual fee paid: {fee_value_as_coin} sats"

        if expected_fee_as_long == fee_value:
            logger.debug(f"The fee matched. {description}")
            return FeeValidationStatus.ACK_FEE_OK

        if expected_fee_as_long < fee_value:
            logger.info(f"The fee was more than what we expected: {description}")
            return FeeValidationStatus.ACK_FEE_OK

        leniency_calc = fee_value / expected_fee_as_long
        if leniency_calc > TxValidator.FEE_TOLERANCE:
            logger.info(f"Leniency rule: the fee was low, but above {TxValidator.FEE_TOLERANCE} of what was expected {leniency_calc} {description}")
            return FeeValidationStatus.ACK_FEE_OK

        result = self._maybe_check_against_fee_from_filter(
            trade_amount,
            is_maker,
            fee_value_as_coin,
            min_fee_param,
            True,
            description
        )
        if result is not None:
            if result:
                return FeeValidationStatus.ACK_FEE_OK 
            elif is_maker:
                return FeeValidationStatus.NACK_MAKER_FEE_TOO_LOW
            else:
                return FeeValidationStatus.NACK_TAKER_FEE_TOO_LOW

        default_fee_param = Param.DEFAULT_MAKER_FEE_BTC if is_maker else Param.DEFAULT_TAKER_FEE_BTC
        if self._fee_exists_using_different_dao_param(trade_amount, fee_value_as_coin, default_fee_param, min_fee_param):
            logger.info(f"Leniency rule: the fee matches a different DAO parameter {description}")
            return FeeValidationStatus.ACK_FEE_OK

        fee_underpaid_message = f"UNDERPAID. {description}"
        logger.info(fee_underpaid_message)
        return (FeeValidationStatus.NACK_MAKER_FEE_TOO_LOW if is_maker 
                else FeeValidationStatus.NACK_TAKER_FEE_TOO_LOW)

    def _check_fee_amount_bsq(self, bsq_tx, trade_amount: Coin, is_maker: bool, block_height: int) -> FeeValidationStatus:
        # TODO: not reached because self.validate_bsq_fee_tx is not implemented
        min_fee_param = Param.MIN_MAKER_FEE_BSQ if is_maker else Param.MIN_TAKER_FEE_BSQ
        expected_fee = self._calculate_fee(
            trade_amount,
            self._get_maker_fee_rate_bsq(block_height) if is_maker else self._get_taker_fee_rate_bsq(block_height),
            min_fee_param
        )
        expected_fee_as_long = expected_fee.value

        fee_value = bsq_tx.get_burnt_bsq()
        logger.debug(f"BURNT BSQ maker fee: {fee_value/100.0} BSQ ({fee_value} sats)")
        description = f"Expected fee: {expected_fee_as_long/100.0:.2f} BSQ, actual fee paid: {fee_value/100.0:.2f} BSQ, Trade amount: {trade_amount.to_plain_string()}"

        if expected_fee_as_long == fee_value:
            logger.debug(f"The fee matched. {description}")
            return FeeValidationStatus.ACK_FEE_OK

        if expected_fee_as_long < fee_value:
            logger.info(f"The fee was more than what we expected. {description} Tx:{bsq_tx.get_id()}")
            return FeeValidationStatus.ACK_FEE_OK

        leniency_calc = fee_value / expected_fee_as_long
        if leniency_calc > TxValidator.FEE_TOLERANCE:
            logger.info(f"Leniency rule: the fee was low, but above {TxValidator.FEE_TOLERANCE} of what was expected {leniency_calc} {description}")
            return FeeValidationStatus.ACK_FEE_OK

        fee_value_as_coin = Coin.value_of(fee_value)

        result = self._maybe_check_against_fee_from_filter(
            trade_amount,
            is_maker,
            fee_value_as_coin,
            min_fee_param,
            False,
            description
        )
        if result is not None:
            if result:
                return FeeValidationStatus.ACK_FEE_OK
            elif is_maker:
                return FeeValidationStatus.NACK_MAKER_FEE_TOO_LOW
            else:
                return FeeValidationStatus.NACK_TAKER_FEE_TOO_LOW

        default_fee_param = Param.DEFAULT_MAKER_FEE_BSQ if is_maker else Param.DEFAULT_TAKER_FEE_BSQ
        if self._fee_exists_using_different_dao_param(trade_amount, Coin.value_of(fee_value), default_fee_param, min_fee_param):
            logger.info(f"Leniency rule: the fee matches a different DAO parameter {description}")
            return FeeValidationStatus.ACK_FEE_OK

        logger.info(description)
        return FeeValidationStatus.NACK_MAKER_FEE_TOO_LOW if is_maker else FeeValidationStatus.NACK_TAKER_FEE_TOO_LOW

    @staticmethod
    def _get_vin_and_vout(json_txt: str) -> tuple[list[dict], list[dict]]:
        # there should always be "vout" at the top level
        # check that there are 2 or 3 vout elements: the fee, the reserved for trade, optional change
        try:
            json_data: dict = json.loads(json_txt)
            if not isinstance(json_data.get("vin", None), list) or not isinstance(
                json_data.get("vout", None), list
            ):
                raise json.JSONDecodeError("missing vin/vout", json_txt, 0)

            json_vin: list[dict] = json_data["vin"]
            json_vout: list[dict] = json_data["vout"]

            if len(json_vin) < 1 or len(json_vout) < 2:
                raise json.JSONDecodeError("not enough vins/vouts", json_txt, 0)

            return json_vin, json_vout

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise json.JSONDecodeError(f"vin/vout parsing error: {str(e)}", json_txt, 0)

    @staticmethod
    def _initial_sanity_checks(tx_id: str, json_txt: str) -> FeeValidationStatus:
        if not json_txt:
            return FeeValidationStatus.NACK_JSON_ERROR

        try:
            json_data: dict[str, Any] = json.loads(json_txt)

            # there should always be "status" container element at the top level
            if json_data.get("status", None) is None:
                return FeeValidationStatus.NACK_JSON_ERROR

            # there should always be "txid" string element at the top level
            if json_data.get("txid", None) is None:
                return FeeValidationStatus.NACK_JSON_ERROR

            # txid should match what we requested
            if tx_id != json_data.get("txid", None):
                return FeeValidationStatus.NACK_JSON_ERROR

            # Check if confirmed field exists in status
            json_status: dict = json_data.get("status", {})
            if json_status.get("confirmed", None) is not None:
                #  the json is valid and it contains a "confirmed" field then tx is known to mempool.space
                #  we don't care if it is confirmed or not, just that it exists.
                return FeeValidationStatus.ACK_FEE_OK

            return FeeValidationStatus.NACK_JSON_ERROR

        except json.JSONDecodeError:
            return FeeValidationStatus.NACK_JSON_ERROR

    @staticmethod
    def _get_tx_confirms(json_txt: str, chain_height: int) -> int:
        block_height = TxValidator._get_tx_block_height(json_txt)
        if block_height > 0:
            return (
                chain_height - block_height
            ) + 1  # if it is in the current block it has 1 conf
        return 0  # 0 indicates unconfirmed

    # this would be useful for the arbitrator verifying that the delayed payout tx is confirmed
    @staticmethod
    def _get_tx_block_height(json_txt: str) -> int:
        try:
            json_data: dict = json.loads(json_txt)
            # there should always be "status" container element at the top level
            if json_data.get("status", None) is None:
                return -1

            json_status: dict = json_data["status"]
            confirmed = json_status.get("confirmed", None)
            if confirmed is None:
                return -1

            if confirmed:
                # it is confirmed, lets get the block height
                block_height = json_status.get("block_height", None)
                if block_height is None:
                    return -1  # block height error
                return int(block_height)

            return 0  # in mempool, not confirmed yet
        except (json.JSONDecodeError, KeyError, TypeError):
            return -1

    # we want the block height applicable for calculating the appropriate expected trading fees
    # if the tx is not yet confirmed, use current block tip, if tx is confirmed use the block it was confirmed at.
    def _get_block_height_for_fee_calculation(self, json_txt: str) -> int:
        # For the maker we set the blockHeightAtOfferCreation from the offer
        if self.fee_payment_block_height > 0:
            return self.fee_payment_block_height

        tx_block_height = self._get_tx_block_height(json_txt)
        if tx_block_height > 0:
            return tx_block_height

        return self.dao_state_service.chain_height

    def _calculate_fee(self, amount: Coin, fee_rate_per_btc: Coin, min_fee_param: Param) -> Coin:
        amount_value = amount.value if amount else 0
        one_btc = Coin.COIN().value
        fact = amount_value / one_btc
        fee_per_btc = Coin.value_of(round(fee_rate_per_btc.value * fact))
        min_fee = self.dao_state_service.get_param_value_as_coin(min_fee_param, min_fee_param.default_value)
        return max(fee_per_btc, min_fee)

    def _get_maker_fee_rate_bsq(self, block_height: int) -> Coin:
        return self.dao_state_service.get_param_value_as_coin(Param.DEFAULT_MAKER_FEE_BSQ, block_height)

    def _get_taker_fee_rate_bsq(self, block_height: int) -> Coin:
        return self.dao_state_service.get_param_value_as_coin(Param.DEFAULT_TAKER_FEE_BSQ, block_height)

    def _get_maker_fee_rate_btc(self, block_height: int) -> Coin:
        return self.dao_state_service.get_param_value_as_coin(Param.DEFAULT_MAKER_FEE_BTC, block_height)

    def _get_taker_fee_rate_btc(self, block_height: int) -> Coin:
        return self.dao_state_service.get_param_value_as_coin(Param.DEFAULT_TAKER_FEE_BTC, block_height)

    def _maybe_check_against_fee_from_filter(
        self,
        trade_amount: Coin,
        is_maker: bool,
        fee_value_as_coin: Coin,
        min_fee_param: Param,
        is_btc_fee: bool,
        description: str
    ) -> Optional[bool]:
        fee_from_filter = self._get_fee_from_filter(is_maker, is_btc_fee)
        if fee_from_filter is None:
            return None
            
        is_valid = self._test_with_fee_from_filter(trade_amount, fee_value_as_coin, fee_from_filter, min_fee_param)
        if not is_valid:
            logger.warning(f"Fee does not match fee from filter. Fee from filter={fee_from_filter}. {description}")
        return is_valid

    def _get_fee_from_filter(self, is_maker: bool, is_btc_fee: bool) -> Optional[Coin]:
        filter = self.filter_manager.get_filter()
        if filter is None:
            return None
            
        if is_maker:
            value = (Coin.value_of(filter.maker_fee_btc) if is_btc_fee 
                    else Coin.value_of(filter.maker_fee_bsq))
        else:
            value = (Coin.value_of(filter.taker_fee_btc) if is_btc_fee 
                    else Coin.value_of(filter.taker_fee_bsq))
            
        return value if value.is_positive() else None

    def _test_with_fee_from_filter(
        self,
        trade_amount: Coin,
        actual_fee_value: Coin,
        fee_from_filter: Coin,
        min_fee_param: Param
    ) -> bool:
        actual_fee_as_long = actual_fee_value.value
        fee_from_filter_as_long = self._calculate_fee(trade_amount, fee_from_filter, min_fee_param).value
        deviation = actual_fee_as_long / fee_from_filter_as_long
        # It can be that the filter has not been updated immediately after DAO param change, so we need a tolerance
        # Common change rate is 15-20%
        return deviation > 0.7

    # implements leniency rule of accepting old DAO rate parameters: https://github.com/bisq-network/bisq/issues/5329#issuecomment-803223859
    # We iterate over all past dao param values and if one of those matches we consider it valid. That covers the non-in-sync cases.
    def _fee_exists_using_different_dao_param(
        self,
        trade_amount: Coin,
        actual_fee_value: Coin,
        default_fee_param: Param,
        min_fee_param: Param
    ) -> bool:
        for dao_historical_rate in self.dao_state_service.get_param_change_list(default_fee_param):
            if actual_fee_value == self._calculate_fee(trade_amount, dao_historical_rate, min_fee_param):
                return True

        # Finally, check the default rate used when we ask for the fee rate at genesis block height 
        # (it is hard coded in the Param enum)
        default_rate = self.dao_state_service.get_param_value_as_coin(
            default_fee_param,
            self.dao_state_service.get_genesis_block_height()
        )
        return actual_fee_value == self._calculate_fee(trade_amount, default_rate, min_fee_param)
