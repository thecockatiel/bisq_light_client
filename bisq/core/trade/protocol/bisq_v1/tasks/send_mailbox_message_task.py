from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from bisq.core.network.p2p.send_mailbox_message_listener import (
    SendMailboxMessageListener,
)
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask

logger = get_logger(__name__)

if TYPE_CHECKING:
    from bisq.core.trade.protocol.bisq_v1.messages.trade_mailbox_message import (
        TradeMailboxMessage,
    )
    from bisq.core.trade.protocol.trade_message import TradeMessage
    from bisq.common.taskrunner.task_runner import TaskRunner
    from bisq.core.trade.model.bisq_v1.trade import Trade


class SendMailboxMessageTask(TradeTask, ABC):

    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)

    @abstractmethod
    def get_trade_mailbox_message(self, id: str) -> "TradeMailboxMessage":
        pass

    @abstractmethod
    def set_state_sent(self) -> None:
        pass

    @abstractmethod
    def set_state_arrived(self) -> None:
        pass

    @abstractmethod
    def set_state_stored_in_mailbox(self) -> None:
        pass

    @abstractmethod
    def set_state_fault(self) -> None:
        pass

    def run(self):
        try:
            self.run_intercept_hook()
            id = self.process_model.offer_id
            self.set_state_sent()
            peers_node_address = self.trade.trading_peer_node_address
            
            message: "TradeMailboxMessage" = self.get_trade_mailbox_message(id)
            
            logger.info(
                f"Send {message.__class__.__name__} to peer {peers_node_address}. "
                f"tradeId={message.trade_id}, uid={message.uid}"
            )
            
            class Listener(SendMailboxMessageListener):
                def on_arrived(self_):
                    logger.info(
                        f"{message.__class__.__name__} arrived at peer {peers_node_address}. "
                        f"tradeId={message.trade_id}, uid={message.uid}"
                    )
                    self.set_state_arrived()
                    self.complete()

                def on_stored_in_mailbox(self_):
                    logger.info(f"{message.__class__.__name__} stored in mailbox for peer {peers_node_address}. tradeId={message.trade_id}, uid={message.uid}")
                    self.on_stored_in_mailbox()
                    
                def on_fault(self_, error_message: str):
                    logger.error(f"{message.__class__.__name__} failed: Peer {peers_node_address}. tradeId={message.trade_id}, uid={message.uid}, errorMessage={error_message}")
                    self.on_fault(error_message, message)

            self.process_model.p2p_service.mailbox_message_service.send_encrypted_mailbox_message(
                peers_node_address,
                self.process_model.trade_peer.pub_key_ring,
                message,
                Listener()
            )
        except Exception as e:
            self.failed(exc=e)

    def on_stored_in_mailbox(self):
        self.set_state_stored_in_mailbox()
        self.complete()

    def on_fault(self, error_message: str, message: "TradeMessage"):
        self.set_state_fault()
        self.append_to_error_message(
            f"Sending message failed: message={message}\nerrorMessage={error_message}"
        )
        self.failed(error_message)
