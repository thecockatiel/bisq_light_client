from bisq.common.setup.log_setup import get_logger
from bisq.core.network.p2p.send_direct_message_listener import SendDirectMessageListener
from bisq.core.trade.protocol.bisq_v1.messages.delayed_payout_tx_signature_request import (
    DelayedPayoutTxSignatureRequest,
)
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from utils.preconditions import check_not_none

logger = get_logger(__name__)


class SellerSendDelayedPayoutTxSignatureRequest(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()

            prepared_delayed_payout_tx = check_not_none(
                self.process_model.prepared_delayed_payout_tx,
                "process_model.prepared_delayed_payout_tx must not be None",
            )
            delayed_payout_tx_signature = check_not_none(
                self.process_model.delayed_payout_tx_signature,
                "process_model.delayed_payout_tx_signature must not be None",
            )
            message = DelayedPayoutTxSignatureRequest(
                trade_id=self.process_model.offer_id,
                sender_node_address=self.process_model.my_node_address,
                delayed_payout_tx=prepared_delayed_payout_tx.bitcoin_serialize(),
                delayed_payout_tx_seller_signature=delayed_payout_tx_signature,
            )

            peers_node_address = self.trade.trading_peer_node_address
            logger.info(
                f"Send {message.__class__.__name__} to peer {peers_node_address}. tradeId={message.trade_id}, uid={message.uid}"
            )

            class Listener(SendDirectMessageListener):

                def on_arrived(self_):
                    logger.info(
                        f"{message.__class__.__name__} arrived at peer {peers_node_address}. tradeId={message.trade_id}, uid={message.uid}"
                    )
                    self.complete()

                def on_fault(self_, error_message: str):
                    logger.error(
                        f"{message.__class__.__name__} failed: Peer {peers_node_address}. "
                        f"tradeId={message.trade_id}, uid={message.uid}, errorMessage={error_message}"
                    )
                    self.append_to_error_message(
                        f"Sending message failed: message={message}\nerrorMessage={error_message}"
                    )
                    self.failed()

            self.process_model.p2p_service.send_encrypted_direct_message(
                peers_node_address,
                self.process_model.trade_peer.pub_key_ring,
                message,
                Listener(),
            )
        except Exception as e:
            self.failed(exc=e)
