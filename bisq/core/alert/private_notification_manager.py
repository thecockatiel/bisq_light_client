from collections.abc import Callable
import contextvars
from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING, Optional
from bisq.common.app.dev_env import DevEnv
from bisq.common.crypto.key_ring import KeyRing
from bisq.common.crypto.pub_key_ring import PubKeyRing
from bisq.core.alert.private_notification_message import PrivateNotificationMessage
from bisq.core.alert.private_notification_payload import PrivateNotificationPayload
from bisq.core.network.p2p.decrypted_message_with_pub_key import (
    DecryptedMessageWithPubKey,
)
from bisq.core.network.p2p.peers.keepalive.messages.ping import Ping
from bisq.core.network.p2p.peers.keepalive.messages.pong import Pong
from bisq.core.network.p2p.send_mailbox_message_listener import (
    SendMailboxMessageListener,
)
from electrum_min.bitcoin import ecdsa_sign_usermessage
from utils.aio import FutureCallback
from utils.data import SimpleProperty
from bisq.common.crypto.encryption import Encryption, ECPrivkey, ECPubkey
from bisq.core.network.p2p.network.message_listener import MessageListener
from concurrent.futures import Future

if TYPE_CHECKING:
    from bisq.core.network.p2p.network.connection import Connection
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.network.p2p.mailbox.mailbox_message_service import (
        MailboxMessageService,
    )
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.common.protocol.network.network_envelope import NetworkEnvelope


class PrivateNotificationManager(MessageListener):

    def __init__(
        self,
        p2p_service: "P2PService",
        network_node: "NetworkNode",
        mailbox_message_service: "MailboxMessageService",
        key_ring: "KeyRing",
        ignore_dev_msg: bool,
        use_dev_privilege_keys: bool,
    ):
        self.logger = get_ctx_logger(__name__)
        self.p2p_service = p2p_service
        self.network_node = network_node
        self.mailbox_message_service = mailbox_message_service
        self.key_ring = key_ring
        self.private_notification_message_property = SimpleProperty[
            "PrivateNotificationPayload"
        ]()
        self.ping_response_handler: Callable[[str], None] = None
        self.private_notification_signing_key: Optional["ECPrivkey"] = None
        self.private_notification_message: Optional["PrivateNotificationMessage"] = None
        self._subscriptions: list[Callable[[], None]] = []

        if not ignore_dev_msg:
            self._subscriptions.append(
                self.p2p_service.add_decrypted_direct_message_listener(
                    self.handle_message
                )
            )
            self._subscriptions.append(
                self.mailbox_message_service.add_decrypted_mailbox_listener(
                    self.handle_message
                )
            )

        # Pub key for developer global privateNotification message
        self.pub_key_as_hex = (
            DevEnv.DEV_PRIVILEGE_PUB_KEY
            if use_dev_privilege_keys
            else "02ba7c5de295adfe57b60029f3637a2c6b1d0e969a8aaefb9e0ddc3a7963f26925"
        )

    def shut_down(self):
        for unsub in self._subscriptions:
            unsub()
        self._subscriptions.clear()
        self.ping_response_handler = None

    def handle_message(
        self,
        decrypted_message_with_pub_key: "DecryptedMessageWithPubKey",
        sender_node_address: "NodeAddress",
    ):
        network_envelope = decrypted_message_with_pub_key.network_envelope
        if isinstance(network_envelope, PrivateNotificationMessage):
            self.logger.info(
                f"Received PrivateNotificationMessage from {sender_node_address} with uid={network_envelope.uid}"
            )
            if network_envelope.sender_node_address == sender_node_address:
                private_notification = network_envelope.private_notification_payload
                if self.verify_signature(private_notification):
                    self.private_notification_message_property.set(private_notification)
            else:
                self.logger.warning(
                    "Peer address not matching for privateNotificationMessage"
                )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def send_private_notification_message_if_key_is_valid(
        self,
        private_notification: "PrivateNotificationPayload",
        pub_key_ring: "PubKeyRing",
        peers_node_address: "NodeAddress",
        priv_key_string: str,
        send_mailbox_message_listener: "SendMailboxMessageListener",
    ) -> bool:
        is_key_valid = self.is_key_valid(priv_key_string)
        if is_key_valid:
            self.sign_and_add_signature_to_private_notification_message(
                private_notification
            )

            message = PrivateNotificationMessage(
                private_notification_payload=private_notification,
                sender_node_address=self.p2p_service.network_node.node_address_property.value,
            )
            self.logger.info(
                f"Send {message.__class__.__name__} to peer {peers_node_address}. uid={message}"
            )
            self.mailbox_message_service.send_encrypted_mailbox_message(
                peers_node_address,
                pub_key_ring,
                message,
                send_mailbox_message_listener,
            )

        return is_key_valid

    def remove_private_notification(self):
        if self.private_notification_message is not None:
            self.mailbox_message_service.remove_mailbox_msg(
                self.private_notification_message
            )

    def is_key_valid(self, priv_key_string: str) -> bool:
        try:
            # TODO: check later for correctness
            self.private_notification_signing_key = (
                Encryption.get_ec_private_key_from_int_hex_string(priv_key_string)
            )
            return (
                self.pub_key_as_hex
                == self.private_notification_signing_key.get_public_key_hex()
            )
        except Exception:
            return False

    def sign_and_add_signature_to_private_notification_message(
        self, private_notification: "PrivateNotificationPayload"
    ):
        message_as_hex = private_notification.message.encode("utf-8").hex()
        # TODO: check later for correctness
        signature = ecdsa_sign_usermessage(
            self.private_notification_signing_key,
            message_as_hex,
            is_compressed=True,
        )

        private_notification.set_sig_and_pub_key(
            signature, self.key_ring.signature_key_pair.public_key
        )

    def verify_signature(
        self, private_notification: "PrivateNotificationPayload"
    ) -> bool:
        message_as_hex = private_notification.message.encode("utf-8").hex()
        try:
            Encryption.verify_ec_message_is_from_pubkey(
                message_as_hex,
                private_notification.signature_as_base64,
                bytes.fromhex(self.pub_key_as_hex),
            )
            return True
        except:
            self.logger.warning("verifySignature failed")
            return False

    def send_ping(
        self, peers_node_address: "NodeAddress", result_handler: Callable[[str], None]
    ):
        ping = Ping()
        self.logger.info(f"Send Ping to peer {peers_node_address}, nonce={ping.nonce}")

        def on_send_complete(connection: "Connection"):
            connection.add_message_listener(self)
            self.ping_response_handler = result_handler

        def on_send_failed(error: "Exception"):
            error_message = (
                f"Sending ping to {peers_node_address.get_host_name_for_display()} failed. "
                f"That is expected if the peer is offline.\n\tping={ping}\n\t"
                f"Exception={str(error)}"
            )
            self.logger.info(error_message)
            result_handler(error_message)

        future = self.network_node.send_message(peers_node_address, ping)

        future.add_done_callback(
            FutureCallback(
                on_send_complete,
                on_send_failed,
            )
        )

    def on_message(self, network_envelope: "NetworkEnvelope", connection: "Connection"):
        if isinstance(network_envelope, Pong):
            key = connection.peers_node_address.get_full_address()
            self.logger.info(f"Received Pong! {network_envelope} from {key}")
            connection.remove_message_listener(self)
            if self.ping_response_handler:
                self.ping_response_handler("SUCCESS")
