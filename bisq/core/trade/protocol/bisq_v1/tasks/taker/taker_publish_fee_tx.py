from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bisq.core.trade.model.trade_state import TradeState
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.common.taskrunner.task_runner import TaskRunner
    from bisq.core.btc.exceptions.tx_broadcast_exception import TxBroadcastException
    from bitcoinj.core.transaction import Transaction


class TakerPublishFeeTx(TradeTask):
    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)
        self.logger = get_ctx_logger(__name__)

    def run(self):
        try:
            self.run_intercept_hook()

            trade_wallet_service = self.process_model.trade_wallet_service
            take_offer_fee_tx = self.process_model.take_offer_fee_tx

            if self.trade.is_currency_for_taker_fee_btc:
                # We committed to be sure the tx gets into the wallet even in the broadcast process it would be
                # committed as well, but if user would close app before success handler returns the commit would not
                # be done.
                trade_wallet_service.commit_tx(take_offer_fee_tx)

                class Listener(TxBroadcasterCallback):
                    def on_success(self_, transaction: "Transaction"):
                        self._on_success(transaction)

                    def on_failure(self_, exception: "TxBroadcastException"):
                        self._on_failure(exception)

                trade_wallet_service.broadcast_tx(
                    take_offer_fee_tx,
                    Listener(),
                )
            else:
                bsq_wallet_service = self.process_model.bsq_wallet_service
                bsq_wallet_service.commit_tx(take_offer_fee_tx, TxType.PAY_TRADE_FEE)
                # We need to create another instance, otherwise the tx would trigger an invalid state exception
                # if it gets committed 2 times
                trade_wallet_service.commit_tx(
                    trade_wallet_service.get_cloned_transaction(take_offer_fee_tx)
                )

                class Listener(TxBroadcasterCallback):
                    def on_success(self_, transaction: "Transaction"):
                        self._on_success(transaction)

                    def on_failure(self_, exception: "TxBroadcastException"):
                        self._on_failure(exception)

                bsq_wallet_service.broadcast_tx(
                    take_offer_fee_tx,
                    Listener(),
                )

        except Exception as e:
            self.failed(exc=e)

    def _on_failure(self, exception: "TxBroadcastException"):
        if not self.completed:
            self.logger.error(str(exception))
            self.trade.error_message = (
                "An error occurred.\n" + "Error message:\n" + str(exception)
            )
            self.failed(exc=exception)
        else:
            self.logger.warning(
                "We got the _on_failure callback called after the timeout has been triggered a complete()."
            )

    def _on_success(self, transaction: "Transaction"):
        if not self.completed:
            if transaction is not None:
                self.trade.taker_fee_tx_id = transaction.get_tx_id()
                self.trade.state_property.value = (
                    TradeState.TAKER_PUBLISHED_TAKER_FEE_TX
                )

                self.process_model.trade_manager.request_persistence()

                self.complete()
        else:
            self.logger.warning(
                "We got the _on_success callback called after the timeout has been triggered a complete()."
            )
