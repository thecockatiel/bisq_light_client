from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.network.p2p.send_direct_message_listener import SendDirectMessageListener
from bisq.core.trade.protocol.bisq_v1.messages.delayed_payout_tx_signature_response import (
    DelayedPayoutTxSignatureResponse,
)
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from utils.preconditions import check_not_none


if TYPE_CHECKING:
    from bisq.common.taskrunner.task_runner import TaskRunner
    from bisq.core.trade.model.bisq_v1.trade import Trade

class BuyerSendsDelayedPayoutTxSignatureResponse(TradeTask):

    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)
        self.logger = get_ctx_logger(__name__)

    def run(self):
        try:
            self.run_intercept_hook()

            delayed_payout_tx_signature = check_not_none(
                self.process_model.delayed_payout_tx_signature
            )

            if self.process_model.deposit_tx is not None:
                # set missing witness to be able to serialize the tx
                missing_idx = []
                for input in self.process_model.deposit_tx.inputs:
                    if input.witness is None:
                        input.witness = b"\x00"
                        missing_idx.append(input.index)

                # set in BuyerAsTakerSignsDepositTx task
                deposit_tx_bytes = self.process_model.deposit_tx.bitcoin_serialize()

                # set the missing witness to None again
                for input in self.process_model.deposit_tx.inputs:
                    if input.index in missing_idx:
                        input.witness = None
            else:
                # set in BuyerAsMakerCreatesAndSignsDepositTx task
                deposit_tx_bytes = self.process_model.prepared_deposit_tx

            message = DelayedPayoutTxSignatureResponse(
                trade_id=self.process_model.offer_id,
                sender_node_address=self.process_model.my_node_address,
                delayed_payout_tx_buyer_signature=delayed_payout_tx_signature,
                deposit_tx=deposit_tx_bytes,
            )

            peers_node_address = self.trade.trading_peer_node_address
            self.logger.info(
                f"Send {message.__class__.__name__} to peer {peers_node_address}. tradeId={message.trade_id}, uid={message.uid}"
            )

            class Listener(SendDirectMessageListener):
                def on_arrived(self_):
                    self.logger.info(
                        f"{message.__class__.__name__} arrived at peer {peers_node_address}. "
                        f"tradeId={message.trade_id}, uid={message.uid}"
                    )
                    self.complete()

                def on_fault(self_, error_message: str):
                    self.logger.error(
                        f"{message.__class__.__name__} failed: Peer {peers_node_address}. "
                        f"tradeId={message.trade_id}, uid={message.uid}, errorMessage={error_message}"
                    )
                    self.append_to_error_message(
                        f"Sending message failed: message={message}\nerrorMessage={error_message}"
                    )
                    self.failed(error_message)

            self.process_model.p2p_service.send_encrypted_direct_message(
                peers_node_address,
                self.process_model.trade_peer.pub_key_ring,
                message,
                Listener(),
            )
        except Exception as e:
            self.failed(exc=e)
