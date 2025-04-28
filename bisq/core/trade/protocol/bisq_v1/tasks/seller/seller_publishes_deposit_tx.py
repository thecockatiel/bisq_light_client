from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
from bisq.core.trade.model.trade_state import TradeState
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.common.taskrunner.task_runner import TaskRunner


class SellerPublishesDepositTx(TradeTask):

    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)
        self.logger = get_ctx_logger(__name__)

    def run(self):
        try:
            self.run_intercept_hook()

            deposit_tx = self.process_model.deposit_tx

            self.process_model.trade_wallet_service.broadcast_tx(
                deposit_tx, _TxCallback(self)
            )
        except Exception as e:
            self.failed(exc=e)


class _TxCallback(TxBroadcasterCallback):

    def __init__(self, task: "SellerPublishesDepositTx"):
        super().__init__()
        self.task = task

    def on_success(self, transaction):
        if not self.task.completed:
            # Now as we have published the deposit tx we set it in trade
            self.task.trade.apply_deposit_tx(transaction)
            self.task.trade.state_property.set(TradeState.SELLER_PUBLISHED_DEPOSIT_TX)
            self.task.process_model.btc_wallet_service.swap_trade_entry_to_available_entry(
                self.task.process_model.offer.id,
                AddressEntryContext.RESERVED_FOR_TRADE,
            )
            self.task.process_model.trade_manager.request_persistence()
            self.task.complete()
        else:
            self.task.logger.warning(
                "We got the onSuccess callback called after the timeout has been triggered a complete()."
            )

    def on_failure(self, exception):
        if not self.task.completed:
            self.task.failed(exc=exception)
        else:
            self.task.logger.warning(
                "We got the onFailure callback called after the timeout has been triggered a complete()."
            )
