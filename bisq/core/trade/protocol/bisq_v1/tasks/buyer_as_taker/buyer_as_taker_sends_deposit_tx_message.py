from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.network.p2p.send_direct_message_listener import SendDirectMessageListener
from bisq.core.trade.protocol.bisq_v1.messages.deposit_tx_message import (
    DepositTxMessage,
)
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask


if TYPE_CHECKING:
    from bisq.common.taskrunner.task_runner import TaskRunner
    from bisq.core.trade.model.bisq_v1.trade import Trade


class BuyerAsTakerSendsDepositTxMessage(TradeTask):

    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)
        self.logger = get_ctx_logger(__name__)

    def run(self):
        try:
            self.run_intercept_hook()

            if self.process_model.deposit_tx is not None:
                # Remove witnesses from the sent deposit_tx, so that the seller can still compute the final
                # tx id, but cannot publish it before providing the buyer with a signed delayed payout tx.
                message = DepositTxMessage(
                    trade_id=self.process_model.offer_id,
                    sender_node_address=self.process_model.my_node_address,
                    deposit_tx_without_witnesses=self.process_model.deposit_tx.bitcoin_serialize(
                        include_sigs=False
                    ),
                )

                peers_node_address = self.trade.trading_peer_node_address
                self.logger.info(
                    f"Send {message.__class__.__name__} to peer {peers_node_address}. trade_id={message.trade_id}, uid={message.uid}"
                )

                class Listener(SendDirectMessageListener):
                    def on_arrived(self_):
                        self.logger.info(
                            f"{message.__class__.__name__} arrived at peer {peers_node_address}. trade_id={message.trade_id}, uid={message.uid}"
                        )
                        self.complete()

                    def on_fault(self_, error_message):
                        self.logger.error(
                            f"{message.__class__.__name__} failed: Peer {peers_node_address}. "
                            f"trade_id={message.trade_id}, uid={message.uid}, error_message={error_message}"
                        )
                        self.append_to_error_message(
                            f"Sending message failed: message={message}\nerror_message={error_message}"
                        )
                        self.failed()

                self.process_model.p2p_service.send_encrypted_direct_message(
                    peers_node_address,
                    self.process_model.trade_peer.pub_key_ring,
                    message,
                    Listener(),
                )
            else:
                self.logger.error(
                    f"self.process_model.deposit_tx = {self.process_model.deposit_tx}",
                )
                self.failed("DepositTx is None")
        except Exception as e:
            self.failed(exc=e)
