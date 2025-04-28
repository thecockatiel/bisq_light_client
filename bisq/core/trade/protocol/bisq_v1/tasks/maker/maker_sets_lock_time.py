from typing import TYPE_CHECKING
from bisq.common.config.config import Config
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.btc.wallet.restrictions import Restrictions
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask

if TYPE_CHECKING:
    from bisq.common.taskrunner.task_runner import TaskRunner
    from bisq.core.trade.model.bisq_v1.trade import Trade


class MakerSetsLockTime(TradeTask):

    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)
        self.logger = get_ctx_logger(__name__)

    def run(self):
        try:
            self.run_intercept_hook()

            # 10 days for altcoins, 20 days for other payment methods
            # For regtest dev environment we use 5 blocks
            delay = (
                5
                if Config.BASE_CURRENCY_NETWORK_VALUE.is_regtest()
                else Restrictions.get_lock_time(
                    self.process_model.offer.payment_method.is_blockchain()
                )
            )

            lock_time = (
                self.process_model.btc_wallet_service.get_best_chain_height() + delay
            )
            self.logger.info(f"lockTime={lock_time}, delay={delay}")
            self.trade.lock_time = lock_time

            self.process_model.trade_manager.request_persistence()

            self.complete()
        except Exception as e:
            self.failed(exc=e)
