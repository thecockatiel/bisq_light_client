from typing import TYPE_CHECKING
import uuid
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.network.p2p.send_mailbox_message_listener import SendMailboxMessageListener
from bisq.core.support.dispute.mediation.mediation_result_state import MediationResultState
from bisq.core.trade.protocol.bisq_v1.messages.mediated_payout_tx_signature_message import MediatedPayoutTxSignatureMessage
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.common.taskrunner.task_runner import TaskRunner


class SendMediatedPayoutSignatureMessage(TradeTask):

    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)
        self.logger = get_ctx_logger(__name__)

    def run(self):
        try:
            self.run_intercept_hook()

            pub_key_ring = self.process_model.pub_key_ring
            contract = self.trade.contract
            assert contract is not None, "contract must not be None"
            
            peers_pub_key_ring = contract.get_peers_pub_key_ring(pub_key_ring)
            peers_node_address = contract.get_peers_node_address(pub_key_ring)
            p2p_service = self.process_model.p2p_service
            
            message = MediatedPayoutTxSignatureMessage(
                tx_signature=self.process_model.mediated_payout_tx_signature,
                trade_id=self.trade.get_id(),
                sender_node_address=p2p_service.address,
                uid=str(uuid.uuid4())
            )
            
            self.logger.info(f"Send {message.__class__.__name__} to peer {peers_node_address}. "
                       f"tradeId={message.trade_id}, uid={message.uid}")

            self.trade.mediation_result_state = MediationResultState.SIG_MSG_SENT
            self.process_model.trade_manager.request_persistence()

            class Listener(SendMailboxMessageListener):
                def on_arrived(self_):
                    self.logger.info(f"{message.__class__.__name__} arrived at peer {peers_node_address}. "
                            f"tradeId={message.trade_id}, uid={message.uid}")
                    self.trade.mediation_result_state = MediationResultState.SIG_MSG_ARRIVED
                    self.process_model.trade_manager.request_persistence()
                    self.complete()

                def on_stored_in_mailbox(self_):
                    self.logger.info(f"{message.__class__.__name__} stored in mailbox for peer {peers_node_address}. "
                            f"tradeId={message.trade_id}, uid={message.uid}")
                    self.trade.mediation_result_state = MediationResultState.SIG_MSG_IN_MAILBOX
                    self.process_model.trade_manager.request_persistence()
                    self.complete()

                def on_fault(self_, error_message):
                    self.logger.error(f"{message.__class__.__name__} failed: Peer {peers_node_address}. "
                            f"tradeId={message.trade_id}, uid={message.uid}, errorMessage={error_message}")
                    self.trade.mediation_result_state = MediationResultState.SIG_MSG_SEND_FAILED
                    self.append_to_error_message(f"Sending message failed: message={message}\nerrorMessage={error_message}")
                    self.process_model.trade_manager.request_persistence()
                    self.failed(error_message)

            p2p_service.mailbox_message_service.send_encrypted_mailbox_message(
                peers_node_address,
                peers_pub_key_ring,
                message,
                Listener()
            )

        except Exception as e:
            self.failed(exc=e)

