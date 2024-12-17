from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import timedelta
from typing import TYPE_CHECKING, Optional, Union
from bisq.common.setup.log_setup import get_logger
from bisq.common.taskrunner.task import Task
from bisq.common.user_thread import UserThread
from bisq.common.timer import Timer
from bisq.core.network.p2p.ack_message_source_type import AckMessageSourceType
from bisq.core.network.p2p.decrypted_direct_message_listener import (
    DecryptedDirectMessageListener,
)
from bisq.core.network.p2p.messaging.decrypted_mailbox_listener import (
    DecryptedMailboxListener,
)
from bisq.core.network.p2p.ack_message import AckMessage
from bisq.core.network.p2p.send_mailbox_message_listener import SendMailboxMessageListener
from bisq.core.trade.protocol.fluent_protocol_condition_result import FluentProtocolConditionResult
from bisq.core.trade.protocol.fluent_protocol_event import FluentProtocolEvent
from bisq.core.trade.protocol.trade_message import TradeMessage
from bisq.core.network.p2p.mailbox.mailbox_message import MailboxMessage
from bisq.core.trade.protocol.fluent_protocol import FluentProtocol
from bisq.core.trade.protocol.fluent_protocol_condition import FluentProtocolCondition
from bisq.core.trade.protocol.fluent_protocol_setup import FluentProtocolSetup

if TYPE_CHECKING:
    from bisq.core.trade.protocol.protocol_model import ProtocolModel
    from bisq.core.trade.protocol.trade_peer import TradePeer
    from bisq.core.trade.model.trade_phase import TradePhase
    from bisq.core.offer.offer import Offer
    from bisq.common.protocol.network.network_envelope import NetworkEnvelope
    from bisq.core.network.p2p.decrypted_message_with_pub_key import (
        DecryptedMessageWithPubKey,
    )
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.trade.model.trade_model import TradeModel
    from bisq.core.trade.protocol.provider import Provider
    from bisq.core.trade.trade_manager import TradeManager

logger = get_logger(__name__)


class TradeProtocol(DecryptedDirectMessageListener, DecryptedMailboxListener, ABC):

    def __init__(self, trade_model: "TradeModel"):
        super().__init__()
        self.trade_model = trade_model
        self.protocol_model: ProtocolModel["TradePeer"] = trade_model.get_trade_protocol_model()
        self.timer: Optional["Timer"] = None

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def initialize(
        self,
        service_provider: "Provider",
        trade_manager: "TradeManager",
        offer: "Offer",
    ) -> None:
        self.protocol_model.apply_transient(service_provider, trade_manager, offer)
        self.on_initialized()

    def on_initialized(self) -> None:
        if not self.trade_model.is_completed():
            self.protocol_model.p2p_service.add_decrypted_direct_message_listener(self)

        mailbox_message_service = (
            self.protocol_model.p2p_service.mailbox_message_service
        )

        # We delay a bit here as the trade_model gets updated from the wallet to update the trade_model
        # state (deposit confirmed) and that happens after our method is called.
        # JAVA TODO: To fix that in a better way we would need to change the order of some routines
        # from the TradeManager, but as we are close to a release I dont want to risk a bigger
        # change and leave that for a later PR
        def delayed_action():
            mailbox_message_service.add_decrypted_mailbox_listener(self)
            self.handle_mailbox_collection(
                mailbox_message_service.get_my_decrypted_mailbox_messages()
            )

        UserThread.run_after(delayed_action, timedelta(milliseconds=100))

    def on_withdraw_completed(self) -> None:
        self.cleanup()

    # Resets a potentially pending protocol
    def reset(self):
        self.trade_model.error_message = "Outdated pending protocol got reset."
        self.protocol_model.p2p_service.remove_decrypted_direct_message_listener(self)

    def on_mailbox_message(
        self, message: "TradeMessage", peer_node_address: "NodeAddress"
    ) -> None:
        logger.info(
            f"Received {message.__class__.__name__} as MailboxMessage from {peer_node_address} with tradeId {message.trade_id} and uid {message.uid}"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DecryptedDirectMessageListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_direct_message(
        self,
        decrypted_message_with_pub_key: "DecryptedMessageWithPubKey",
        peer: "NodeAddress",
    ) -> None:
        network_envelope = decrypted_message_with_pub_key.network_envelope
        if not self.is_my_message(network_envelope):
            return

        if not self.is_pub_key_valid(decrypted_message_with_pub_key):
            return

        if isinstance(network_envelope, TradeMessage):
            self.on_trade_message(network_envelope, peer)
        elif isinstance(network_envelope, AckMessage):
            self.on_ack_message(network_envelope, peer)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DecryptedMailboxListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_mailbox_message_added(
        self,
        decrypted_message_with_pub_key: "DecryptedMessageWithPubKey",
        peer: "NodeAddress",
    ) -> None:
        self.handle_mailbox_collection([decrypted_message_with_pub_key])

    def handle_mailbox_collection(
        self, collection: list["DecryptedMessageWithPubKey"]
    ) -> None:
        for msg in collection:
            if not self.is_pub_key_valid(msg):
                continue

            network_envelope = msg.network_envelope
            if not self.is_my_message(network_envelope):
                continue

            if isinstance(network_envelope, MailboxMessage):
                self.handle_mailbox_message(network_envelope)

    def handle_mailbox_message(self, mailbox_message: "MailboxMessage") -> None:
        if isinstance(mailbox_message, TradeMessage):
            # We only remove here if we have already completed the trade_model
            # Otherwise removal is done after successfully applied the task runner
            if self.trade_model.is_completed():
                self.protocol_model.p2p_service.mailbox_message_service.remove_mailbox_msg(
                    mailbox_message
                )
                logger.info(
                    f"Remove {mailbox_message.__class__.__name__} from the P2P network as trade_model is already completed."
                )
                return
            self.on_mailbox_message(
                mailbox_message, mailbox_message.sender_node_address
            )
        elif isinstance(mailbox_message, AckMessage):
            if not self.trade_model.is_completed():
                # We only apply the msg if we have not already completed the trade_model
                self.on_ack_message(
                    mailbox_message, mailbox_message.sender_node_address
                )

            # In any case we remove the msg
            self.protocol_model.p2p_service.mailbox_message_service.remove_mailbox_msg(
                mailbox_message
            )
            logger.info(
                f"Remove {mailbox_message.__class__.__name__} from the P2P network."
            )

    def remove_mailbox_message_after_processing(
        self, trade_message: "TradeMessage"
    ) -> None:
        if isinstance(trade_message, MailboxMessage):
            self.protocol_model.p2p_service.mailbox_message_service.remove_mailbox_msg(
                trade_message
            )
            logger.info(
                f"Remove {trade_message.__class__.__name__} from the P2P network."
            )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Abstract
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @abstractmethod
    def on_trade_message(self, message: "TradeMessage", peer: "NodeAddress") -> None:
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // FluentProtocol
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # We log an error if condition is not met and call the protocol error handler
    def expect(self, condition: "FluentProtocolCondition") -> "FluentProtocol":
        def result_handler(result: "FluentProtocolConditionResult"):
            if not result.is_valid:
                logger.warning(result.info)
                self.handle_task_runner_fault(message=None, source=result.name, error_message=result.info)
                
        return FluentProtocol(self).with_condition(condition).with_result_handler(result_handler)

    # We execute only if condition is met but do not log an error.
    def given(self, condition: "FluentProtocolCondition") -> "FluentProtocol":
        return FluentProtocol(self).with_condition(condition)

    def phase(self, expected_phase: "TradePhase") -> "FluentProtocolCondition":
        return FluentProtocolCondition(self.trade_model).add_phase(expected_phase)

    def any_phase(self, *expected_phases: "TradePhase") -> "FluentProtocolCondition":
        return FluentProtocolCondition(self.trade_model).add_phases(*expected_phases)

    def precondition(self, pre_condition: bool, condition_failed_handler: Optional[Callable[[], None]] = None) -> "FluentProtocolCondition":
        return FluentProtocolCondition(self.trade_model).add_precondition(pre_condition, condition_failed_handler)

    def tasks(self, *tasks: type["Task"]) -> "FluentProtocolSetup":
        return FluentProtocolSetup(self, self.trade_model).with_tasks(*tasks)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // ACK msg
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    @abstractmethod
    def on_ack_message(self, message: "AckMessage", peer: "NodeAddress") -> None:
        pass

    def send_ack_message(self, message: "TradeMessage", result: bool, error_message: Optional[str] = None) -> None:
        peers_pub_key_ring = self.protocol_model.trade_peer.pub_key_ring
        if peers_pub_key_ring is None:
            logger.error("We cannot send the ACK message as peers_pub_key_ring is None")
            return

        trade_id = message.trade_id
        source_uid = message.uid
        ack_message = AckMessage(
            sender_node_address=self.protocol_model.my_node_address,
            source_type=AckMessageSourceType.TRADE_MESSAGE,
            source_msg_class_name=message.__class__.__name__,
            source_uid=source_uid,
            source_id=trade_id,
            success=result,
            error_message=error_message
        )

        # If there was an error during offer verification, the trading_peer_node_address of the trade_model might not be set yet.
        # We can find the peer's node address in the protocol_model's temp_trading_peer_node_address in that case.
        peer = (self.trade_model.trading_peer_node_address if self.trade_model.trading_peer_node_address 
                else self.protocol_model.temp_trading_peer_node_address)

        logger.info(
            f"Send AckMessage for {ack_message.source_msg_class_name} to peer {peer}. "
            f"tradeId={trade_id}, sourceUid={source_uid}"
        )

        class AckMessageListener(SendMailboxMessageListener):
            def on_arrived(self):
                logger.info(
                    f"AckMessage for {ack_message.source_msg_class_name} arrived at peer {peer}. "
                    f"tradeId={trade_id}, sourceUid={source_uid}"
                )

            def on_stored_in_mailbox(self):
                logger.info(
                    f"AckMessage for {ack_message.source_msg_class_name} stored in mailbox for peer {peer}. "
                    f"tradeId={trade_id}, sourceUid={source_uid}"
                )

            def on_fault(self, error_msg: str):
                logger.error(
                    f"AckMessage for {ack_message.source_msg_class_name} failed. Peer {peer}. "
                    f"tradeId={trade_id}, sourceUid={source_uid}, errorMessage={error_msg}"
                )

        self.protocol_model.p2p_service.mailbox_message_service.send_encrypted_mailbox_message(
            peer,
            peers_pub_key_ring,
            ack_message,
            AckMessageListener()
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Timeout
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def start_timeout(self, timeout_sec: float) -> None:
        self.stop_timeout()

        def on_timeout():
            logger.error(
                f"Timeout reached. TradeID={self.trade_model.get_id()}, "
                f"state={self.trade_model.get_trade_state()}, "
                f"timeoutSec={timeout_sec}"
            )
            self.trade_model.error_message = f"Timeout reached. Protocol did not complete in {timeout_sec} sec."
            
            self.protocol_model.trade_manager.request_persistence()
            self.cleanup()

        self.timer = UserThread.run_after(on_timeout, timedelta(seconds=timeout_sec))

    def stop_timeout(self) -> None:
        if self.timer is not None:
            self.timer.stop()
            self.timer = None
            
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Task runner
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    
    def handle_task_runner_success(self, message: Union[Optional["TradeMessage"], "FluentProtocolEvent"], source: Optional[str] = None) -> None:
        if isinstance(message, FluentProtocolEvent):
            source = message.name
            message = None
        elif source is None and message is not None:
            source = message.__class__.__name__
        
        if message is None and source is None:
            raise ValueError("Either message or source must be set.")
            
        logger.info(
            f"TaskRunner successfully completed. Triggered from {source}, "
            f"tradeId={self.trade_model.get_id()}"
        )
        if message is not None:
            self.send_ack_message(message, True)
            
            # Once a taskRunner is completed we remove the mailbox message. To not remove it directly at the task
            # adds some resilience in case of minor errors, so after a restart the mailbox message can be applied
            # again.
            self.remove_mailbox_message_after_processing(message)

    def handle_task_runner_fault(
        self, *, message: Union[Optional["TradeMessage"], "FluentProtocolEvent", None], source: Optional[str] = None, error_message: str
    ) -> None:
        if isinstance(message, FluentProtocolEvent):
            source = message.name
            message = None
        elif source is None and message is not None:
            source = message.__class__.__name__

        if message is None and source is None:
            raise ValueError("Either message or source must be set.")
        
        logger.error(
            f"Task runner failed with error {error_message}. Triggered from {source}"
        )
        
        if message is not None:
            self.send_ack_message(message, False, error_message)
        
        self.cleanup()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Validation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def is_pub_key_valid(self, message: "DecryptedMessageWithPubKey") -> bool:
        # We can only validate the peers pubKey if we have it already. If we are the taker we get it from the offer
        # Otherwise it depends on the state of the tradeModel protocol if we have received the peers pubKeyRing already.
        peers_pub_key_ring = self.protocol_model.trade_peer.pub_key_ring
        is_valid = True
        if (peers_pub_key_ring is not None and 
                message.signature_pub_key != peers_pub_key_ring.signature_pub_key):
            is_valid = False
            logger.error("SignaturePubKey in message does not match the SignaturePubKey we have set for our trading peer.")
        return is_valid

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////
        
    def is_my_message(self, message: "NetworkEnvelope") -> bool:
        if isinstance(message, TradeMessage):
            return message.trade_id == self.trade_model.get_id()
        elif isinstance(message, AckMessage):
            return (message.source_type == AckMessageSourceType.TRADE_MESSAGE and
                    message.source_id == self.trade_model.get_id())
        return False

    def cleanup(self) -> None:
        self.stop_timeout()
        # We do not remove the decrypted_direct_message_listener as in case of not critical failures 
        # we want to allow receiving follow-up messages still