from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.trade.bisq_v1.trade_data_validation import TradeDataValidation
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from utils.preconditions import check_not_none

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.common.taskrunner.task_runner import TaskRunner


class SellerCreatesDelayedPayoutTx(TradeTask):

    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)
        self.logger = get_ctx_logger(__name__)

    def run(self):
        try:
            self.run_intercept_hook()

            tradeWalletService = self.process_model.trade_wallet_service
            deposit_tx = check_not_none(self.process_model.deposit_tx)
            input_amount = deposit_tx.outputs[0].value
            trade_tx_fee_as_long = self.trade.trade_tx_fee_as_long
            selection_height = self.process_model.burning_man_selection_height
            delayed_payout_tx_receivers = (
                self.process_model.delayed_payout_tx_receiver_service.get_receivers(
                    selection_height, input_amount, trade_tx_fee_as_long
                )
            )
            self.logger.info(
                f"Create delayedPayoutTx using selectionHeight {selection_height} and receivers {delayed_payout_tx_receivers}"
            )
            lock_time = self.trade.lock_time
            prepared_delayed_payout_tx = (
                tradeWalletService.create_delayed_unsigned_payout_tx(
                    deposit_tx, delayed_payout_tx_receivers, lock_time
                )
            )

            TradeDataValidation.validate_delayed_payout_tx(
                self.trade,
                prepared_delayed_payout_tx,
                self.process_model.btc_wallet_service,
            )

            self.process_model.prepared_delayed_payout_tx = prepared_delayed_payout_tx

            self.process_model.trade_manager.request_persistence()

            self.complete()
        except Exception as e:
            self.failed(exc=e)
