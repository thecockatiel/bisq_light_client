from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask

if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.common.taskrunner.task_runner import TaskRunner


logger = get_logger(__name__)

class PublishedDelayedPayoutTx(TradeTask):
    
    def __init__(self, task_handler: "TaskRunner[Trade]", trade: "Trade"):
        super().__init__(task_handler, trade)

    def run(self):
        try:
            self.run_intercept_hook()

            delayed_payout_tx = self.trade.get_delayed_payout_tx()
            btc_wallet_service = self.process_model.btc_wallet_service

            # We have spent the funds from the deposit tx with the delayedPayoutTx
            btc_wallet_service.reset_coin_locked_in_multi_sig_address_entry(self.trade.get_id())
            # We might receive funds on AddressEntry.Context.TRADE_PAYOUT so we don't swap that

            committed_delayed_payout_tx = WalletService.maybe_add_self_tx_to_wallet(
                delayed_payout_tx, 
                btc_wallet_service.get_wallet()
            )

            class BroadcastCallback(TxBroadcasterCallback):
                def on_success(self_, transaction: "Transaction"):
                    logger.info(f"publishDelayedPayoutTx onSuccess {transaction}")
                    self.complete()

                def on_failure(self_, exception: Exception):
                    logger.error("publishDelayedPayoutTx onFailure", exc_info=exception)
                    self.failed(exc=exception)

            self.process_model.trade_wallet_service.broadcast_tx(
                committed_delayed_payout_tx, 
                BroadcastCallback()
            )

        except Exception as e:
            self.failed(exc=e)

