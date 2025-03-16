from abc import ABC, abstractmethod
from datetime import timedelta
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.locale.res import Res
from bisq.core.network.p2p.send_mailbox_message_listener import SendMailboxMessageListener
from utils.concurrency import ThreadSafeSet
from bisq.core.support.messages.support_message import SupportMessage
from bisq.core.network.p2p.ack_message import AckMessage

if TYPE_CHECKING:
    from bisq.core.network.p2p.ack_message_source_type import AckMessageSourceType
    from bisq.core.support.messages.chat_messsage import ChatMessage
    from bisq.core.support.support_type import SupportType
    from bisq.common.crypto.pub_key_ring import PubKeyRing
    from bisq.common.timer import Timer
    from bisq.core.btc.setup.wallets_setup import WalletsSetup
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.network.p2p.decrypted_message_with_pub_key import (
        DecryptedMessageWithPubKey,
    )
    from bisq.core.network.p2p.node_address import NodeAddress

logger = get_logger(__name__)

class SupportManager(ABC):

    def __init__(self, p2p_service: "P2PService", wallets_setup: "WalletsSetup"):
        super().__init__()
        self.p2p_service = p2p_service
        self.wallets_setup = wallets_setup

        self.mailbox_message_service = self.p2p_service.mailbox_message_service

        self.delay_msg_map = dict[str, "Timer"]()
        self.decryped_mailbox_message_with_pub_keys = ThreadSafeSet[
            "DecryptedMessageWithPubKey"
        ]()
        self.decryped_direct_message_with_pub_keys = ThreadSafeSet[
            "DecryptedMessageWithPubKey"
        ]()

        self.all_services_initialized = False

        def on_decrypted_direct_message(
            message: "DecryptedMessageWithPubKey", node: "NodeAddress"
        ):
            self.decryped_direct_message_with_pub_keys.add(message)
            self.try_apply_messages()

        self.p2p_service.add_decrypted_direct_message_listener(
            on_decrypted_direct_message
        )

        def on_decrypted_mailbox_message(
            message: "DecryptedMessageWithPubKey", node: "NodeAddress"
        ):
            self.decryped_mailbox_message_with_pub_keys.add(message)
            self.try_apply_messages()

        self.mailbox_message_service.add_decrypted_mailbox_listener(
            on_decrypted_mailbox_message
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Abstract methods
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @abstractmethod
    def on_support_message(self, network_envelope: "SupportMessage") -> None:
        pass

    @abstractmethod
    def get_peer_node_address(self, message: "ChatMessage") -> "NodeAddress":
        pass

    @abstractmethod
    def get_peer_pub_key_ring(self, message: "ChatMessage") -> "PubKeyRing":
        pass

    @abstractmethod
    def get_support_type(self) -> "SupportType":
        pass

    @abstractmethod
    def channel_open(self, message: "ChatMessage") -> bool:
        pass

    @abstractmethod
    def get_all_chat_messages(self, trade_id: str) -> list["ChatMessage"]:
        pass

    @abstractmethod
    def add_and_persist_chat_message(self, message: "ChatMessage") -> None:
        pass

    @abstractmethod
    def request_persistence(self) -> None:
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Delegates p2pService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def is_bootstrapped(self) -> bool:
        return self.p2p_service.is_bootstrapped

    def get_my_address(self) -> "NodeAddress":
        return self.p2p_service.address

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_all_services_initialized(self):
        self.all_services_initialized = True
        
    def try_apply_messages(self):
        if self.is_ready:
            self.apply_messages()
            
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Message handler
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_chat_message(self, chat_message: "ChatMessage") -> None:
        trade_id = chat_message.trade_id
        uid = chat_message.uid
        channel_open = self.channel_open(chat_message)
        
        if not channel_open:
            logger.debug(f"We got a chatMessage but we don't have a matching chat. TradeId = {trade_id}")
            if uid not in self.delay_msg_map:
                timer = UserThread.run_after(lambda: self.on_chat_message(chat_message), timedelta(seconds=1))
                self.delay_msg_map[uid] = timer
            else:
                logger.warning(f"We got a chatMessage after we already repeated to apply the message after a delay. That should never happen. TradeId = {trade_id}")
            return

        self.cleanup_retry_map(uid)
        receiver_pub_key_ring = self.get_peer_pub_key_ring(chat_message)

        self.add_and_persist_chat_message(chat_message)

        # We never get a errorMessage in that method (only if we cannot resolve the receiverPubKeyRing but then we
        # cannot send it anyway)
        if receiver_pub_key_ring is not None:
            self.send_ack_message(chat_message, receiver_pub_key_ring, True, None)

    def on_ack_message(self, ack_message: "AckMessage") -> None:
        if ack_message.source_type == self.get_ack_message_source_type():
            if ack_message.success:
                logger.info(
                    f"Received AckMessage for {ack_message.source_msg_class_name} "
                    f"with tradeId {ack_message.source_id} and uid {ack_message.source_uid}"
                )
            else:
                logger.warning(
                    f"Received AckMessage with error state for {ack_message.source_msg_class_name} "
                    f"with tradeId {ack_message.source_id} and errorMessage={ack_message.error_message}"
                )

            for msg in self.get_all_chat_messages(ack_message.source_id):
                if msg.uid == ack_message.source_uid:
                    if ack_message.success:
                        msg.acknowledged_property.value = True
                    else:
                        msg.ack_error_property.value = ack_message.error_message
            
            self.request_persistence()

    @abstractmethod
    def get_ack_message_source_type(self) -> "AckMessageSourceType":
        pass
    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Send message
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def send_chat_message(self, message: "ChatMessage") -> "ChatMessage":
        peers_node_address = self.get_peer_node_address(message)
        receiver_pub_key_ring = self.get_peer_pub_key_ring(message)
        
        if peers_node_address is None or receiver_pub_key_ring is None:
            UserThread.run_after(lambda: message.send_message_error_property.set(Res.get("support.receiverNotKnown")), timedelta(seconds=1))
        else:
            logger.info(
                f"Send {message.__class__.__name__} to peer {peers_node_address}. "
                f"tradeId={message.trade_id}, uid={message.uid}"
            )

            outer = self
            
            class MailboxListener(SendMailboxMessageListener):
                def on_arrived(self):
                    logger.info(
                        f"{message.__class__.__name__} arrived at peer {peers_node_address}. "
                        f"tradeId={message.trade_id}, uid={message.uid}"
                    )
                    message.arrived_property.value = True
                    outer.request_persistence()

                def on_stored_in_mailbox(self):
                    logger.info(
                        f"{message.__class__.__name__} stored in mailbox for peer {peers_node_address}. "
                        f"tradeId={message.trade_id}, uid={message.uid}"
                    )
                    message.stored_in_mailbox_property.value = True
                    outer.request_persistence()

                def on_fault(self, error_message: str):
                    logger.error(
                        f"{message.__class__.__name__} failed: Peer {peers_node_address}. "
                        f"tradeId={message.trade_id}, uid={message.uid}, errorMessage={error_message}"
                    )
                    message.send_message_error_property.value = error_message
                    outer.request_persistence()

            self.mailbox_message_service.send_encrypted_mailbox_message(
                peers_node_address,
                receiver_pub_key_ring,
                message,
                MailboxListener()
            )

        return message

    def send_ack_message(
        self,
        support_message: "SupportMessage",
        peers_pub_key_ring: "PubKeyRing",
        result: bool,
        error_message: Optional[str] = None
    ) -> None:
        trade_id = support_message.get_trade_id()
        uid = support_message.uid
        ack_message = AckMessage(
            sender_node_address=self.p2p_service.network_node.node_address_property.value,
            source_type=self.get_ack_message_source_type(),
            source_msg_class_name=support_message.__class__.__name__,
            source_uid=uid,
            source_id=trade_id,
            success=result, 
            error_message=error_message,
        )
        peers_node_address = support_message.sender_node_address
        
        logger.info(
            f"Send AckMessage for {ack_message.source_msg_class_name} to peer {peers_node_address}. "
            f"tradeId={trade_id}, uid={uid}"
        )

        class AckMailboxListener(SendMailboxMessageListener):
            def on_arrived(self):
                logger.info(
                    f"AckMessage for {ack_message.source_msg_class_name} arrived at peer {peers_node_address}. "
                    f"tradeId={trade_id}, uid={uid}"
                )

            def on_stored_in_mailbox(self):
                logger.info(
                    f"AckMessage for {ack_message.source_msg_class_name} stored in mailbox for peer {peers_node_address}. "
                    f"tradeId={trade_id}, uid={uid}"
                )

            def on_fault(self, error_message: str):
                logger.error(
                    f"AckMessage for {ack_message.source_msg_class_name} failed. Peer {peers_node_address}. "
                    f"tradeId={trade_id}, uid={uid}, errorMessage={error_message}"
                )

        self.mailbox_message_service.send_encrypted_mailbox_message(
            peers_node_address,
            peers_pub_key_ring,
            ack_message,
            AckMailboxListener()
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Protected
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def can_process_message(self, message: "SupportMessage") -> bool:
        return message.support_type == self.get_support_type()

    def cleanup_retry_map(self, uid: str) -> None:
        if uid in self.delay_msg_map:
            timer = self.delay_msg_map.pop(uid)
            if timer is not None:
                timer.stop()

    @property
    def is_ready(self) -> bool:
        return (self.all_services_initialized and
                self.p2p_service.is_bootstrapped and
                self.wallets_setup.is_download_complete and
                self.wallets_setup.has_sufficient_peers_for_broadcast)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def apply_messages(self) -> None:
        for decrypted_message_with_pub_key in self.decryped_direct_message_with_pub_keys:
            network_envelope = decrypted_message_with_pub_key.network_envelope
            if isinstance(network_envelope, SupportMessage):
                self.on_support_message(network_envelope)
            elif isinstance(network_envelope, AckMessage):
                self.on_ack_message(network_envelope)
        self.decryped_direct_message_with_pub_keys.clear()

        for decrypted_message_with_pub_key in self.decryped_mailbox_message_with_pub_keys:
            network_envelope = decrypted_message_with_pub_key.network_envelope
            logger.trace(f"## decryptedMessageWithPubKey message={network_envelope.__class__.__name__}")
            if isinstance(network_envelope, SupportMessage):
                self.on_support_message(network_envelope)
                self.mailbox_message_service.remove_mailbox_msg(network_envelope)
            elif isinstance(network_envelope, AckMessage):
                self.on_ack_message(network_envelope)
                self.mailbox_message_service.remove_mailbox_msg(network_envelope)
        self.decryped_mailbox_message_with_pub_keys.clear()

