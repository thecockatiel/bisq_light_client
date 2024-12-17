from typing import TYPE_CHECKING
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.trade.protocol.bisq_v1.messages.peer_published_delayed_payout_tx_message import PeerPublishedDelayedPayoutTxMessage
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bisq.core.util.validator import Validator

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.common.taskrunner.task_runner import TaskRunner

class ProcessPeerPublishedDelayedPayoutTxMessage(TradeTask):
    
    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)

    def run(self):
        try:
            self.run_intercept_hook()

            message = self.process_model.trade_message
            if not isinstance(message, PeerPublishedDelayedPayoutTxMessage):
                raise ValueError(f"Invalid message type. expected type: PeerPublishedDelayedPayoutTxMessage, actual type: {type(message)}")
            
            Validator.check_trade_id(self.process_model.offer_id, message)
            assert message is not None

            # update to the latest peer address of our peer if the message is correct
            self.trade.trading_peer_node_address = self.process_model.temp_trading_peer_node_address

            # We add the tx to our wallet
            delayed_payout_tx = self.trade.get_delayed_payout_tx()
            assert delayed_payout_tx is not None
                
            WalletService.maybe_add_self_tx_to_wallet(
                delayed_payout_tx, 
                self.process_model.btc_wallet_service.get_wallet()
            )

            self.process_model.trade_manager.request_persistence()

            self.complete()
        except Exception as e:
            self.failed(exc=e)

