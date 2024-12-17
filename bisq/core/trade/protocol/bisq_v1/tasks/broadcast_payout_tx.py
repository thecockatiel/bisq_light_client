from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bitcoinj.core.transaction_confidence_type import TransactionConfidenceType

if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bisq.core.btc.exceptions.tx_broadcast_exception import TxBroadcastException
    from bisq.common.taskrunner.task_runner import TaskRunner
    from bisq.core.trade.model.bisq_v1.trade import Trade
    
logger = get_logger(__name__)

class BroadcastPayoutTx(TradeTask, ABC):
    
    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)
        
    @abstractmethod
    def set_state(self) -> None:
        pass
        
    def run(self) -> None:
        try:
            self.run_intercept_hook()
            payout_tx = self.trade.get_payout_tx()
            assert payout_tx is not None, "payoutTx must not be None"

            confidence_type = payout_tx.get_confidence().confidence_type
            logger.debug(f"payoutTx confidenceType: {confidence_type}")
            
            if (confidence_type == TransactionConfidenceType.BUILDING or 
                confidence_type == TransactionConfidenceType.PENDING):
                logger.debug(f"payoutTx was already published. confidenceType: {confidence_type}")
                self.set_state()
                self.complete()
            else:
                class TxCallback(TxBroadcasterCallback):
                    def on_success(transaction: "Transaction") -> None:
                        if not self.completed:
                            logger.debug(f"BroadcastTx succeeded. Transaction: {transaction}")
                            self.set_state()
                            self.complete()
                        else:
                            logger.warning("We got the onSuccess callback called after the timeout has been triggered a complete().")

                    def on_failure(exception: "TxBroadcastException") -> None:
                        if not self.completed:
                            logger.error(f"BroadcastTx failed. Error: {exception}")
                            self.failed(exc=exception)
                        else:
                            logger.warning("We got the onFailure callback called after the timeout has been triggered a complete().")
                    
                self.process_model.trade_wallet_service.broadcast_tx(payout_tx, TxCallback())
                
        except Exception as e:
            self.failed(exc=e)


