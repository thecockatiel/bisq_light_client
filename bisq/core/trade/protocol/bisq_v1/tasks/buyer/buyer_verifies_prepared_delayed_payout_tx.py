from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.trade.bisq_v1.trade_data_validation import TradeDataValidation
from bisq.core.trade.bisq_v1.trade_data_validation_exception import (
    TradeDataValidationException,
)
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from utils.preconditions import check_not_none

if TYPE_CHECKING:
    from bisq.common.taskrunner.task_runner import TaskRunner
    from bisq.core.trade.model.bisq_v1.trade import Trade


class BuyerVerifiesPreparedDelayedPayoutTx(TradeTask):

    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)
        self.logger = get_ctx_logger(__name__)

    def run(self):
        try:
            self.run_intercept_hook()

            sellers_prepared_delayed_payout_tx = check_not_none(
                self.process_model.prepared_delayed_payout_tx
            )
            btc_wallet_service = self.process_model.btc_wallet_service
            TradeDataValidation.validate_delayed_payout_tx(
                self.trade, sellers_prepared_delayed_payout_tx, btc_wallet_service
            )

            prepared_deposit_tx = btc_wallet_service.get_tx_from_serialized_tx(
                self.process_model.prepared_deposit_tx
            )
            input_amount = prepared_deposit_tx.outputs[0].value
            trade_tx_fee = self.trade.trade_tx_fee_as_long
            delayed_payout_tx_receivers = (
                self.process_model.delayed_payout_tx_receiver_service.get_receivers(
                    self.process_model.burning_man_selection_height,
                    input_amount,
                    trade_tx_fee,
                )
            )

            lock_time = self.trade.lock_time
            buyers_prepared_delayed_payout_tx = self.process_model.trade_wallet_service.create_delayed_unsigned_payout_tx(
                prepared_deposit_tx, delayed_payout_tx_receivers, lock_time
            )
            if (
                buyers_prepared_delayed_payout_tx.get_tx_id()
                != sellers_prepared_delayed_payout_tx.get_tx_id()
            ):
                error_msg = "TxIds of buyers_prepared_delayed_payout_tx and sellers_prepared_delayed_payout_tx must be the same."
                self.logger.error(
                    f"{error_msg} \n"
                    f"buyers_prepared_delayed_payout_tx={buyers_prepared_delayed_payout_tx}, \n"
                    f"sellers_prepared_delayed_payout_tx={sellers_prepared_delayed_payout_tx}, \n"
                    f"BtcWalletService.chain_height={self.process_model.btc_wallet_service.get_best_chain_height()}, \n"
                    f"DaoState.chain_height={self.process_model.dao_facade.chain_height}, \n"
                    f"is_dao_state_in_sync={self.process_model.dao_facade.is_dao_state_ready_and_in_sync}"
                )
                raise IllegalArgumentException(error_msg)

            # If the deposit tx is non-malleable, we already know its final ID, so should check that now
            # before sending any further data to the seller, to provide extra protection for the buyer.
            if self._is_deposit_tx_non_malleable():
                TradeDataValidation.validate_payout_tx_input(
                    prepared_deposit_tx, sellers_prepared_delayed_payout_tx
                )
            else:
                self.logger.info(
                    "Deposit tx is malleable, so we skip sellers_prepared_delayed_payout_tx input validation."
                )

            self.complete()
        except TradeDataValidationException as e:
            self.failed(str(e))
        except Exception as e:
            self.failed(exc=e)

    def _is_deposit_tx_non_malleable(self):
        buyer_inputs = check_not_none(self.process_model.raw_transaction_inputs)
        seller_inputs = check_not_none(
            self.process_model.trade_peer.raw_transaction_inputs
        )

        return all(
            self.process_model.trade_wallet_service.is_p2wh(input)
            for input in buyer_inputs
        ) and all(
            self.process_model.trade_wallet_service.is_p2wh(input)
            for input in seller_inputs
        )
