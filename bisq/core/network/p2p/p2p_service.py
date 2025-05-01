from collections.abc import Callable
from concurrent.futures import Future
from datetime import timedelta
from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING, Optional
from bisq.common.capabilities import Capabilities
from bisq.common.crypto.crypto_exception import CryptoException
from bisq.common.crypto.pub_key_ring import PubKeyRing
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.common.protocol.protobuffer_exception import ProtobufferException
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.network.close_connection_reason import CloseConnectionReason
from bisq.core.network.p2p.network.connection import Connection
from bisq.core.network.p2p.network.connection_listener import ConnectionListener
from bisq.core.network.p2p.network.message_listener import MessageListener
from bisq.core.network.p2p.network.setup_listener import SetupListener
from bisq.core.network.p2p.network_not_ready_exception import NetworkNotReadyException
from bisq.core.network.p2p.peers.getdata.request_data_manager import RequestDataManager
from bisq.core.network.p2p.prefixed_sealed_and_signed_message import (
    PrefixedSealedAndSignedMessage,
)
from bisq.core.network.p2p.send_direct_message_listener import SendDirectMessageListener
from bisq.core.network.utils.capability_utils import CapabilityUtils
from utils.aio import FutureCallback
from utils.concurrency import ThreadSafeSet
from utils.data import (
    SimpleProperty,
    SimplePropertyChangeEvent,
    combine_simple_properties,
)
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.network.p2p.storage.payload.persistable_network_payload import (
        PersistableNetworkPayload,
    )
    from bisq.core.network.p2p.storage.payload.protected_storage_payload import (
        ProtectedStoragePayload,
    )
    from bisq.core.network.socks5_proxy_provider import Socks5ProxyProvider
    from bisq.core.network.p2p.peers.broadcaster import Broadcaster
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.network.p2p.decrypted_direct_message_listener import (
        DecryptedDirectMessageListener,
    )
    from bisq.core.network.p2p.peers.keepalive.keep_alive_manager import (
        KeepAliveManager,
    )
    from bisq.core.network.p2p.storage.p2p_data_storage import P2PDataStorage
    from bisq.core.network.p2p.p2p_service_listener import P2PServiceListener
    from bisq.core.network.p2p.peers.peer_manager import PeerManager
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.crypto.encryption_service import EncryptionService
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.network.p2p.mailbox.mailbox_message_service import (
        MailboxMessageService,
    )
    from bisq.core.network.p2p.peers.peerexchange.peer_exchange_manager import (
        PeerExchangeManager,
    )
    from bisq.core.network.p2p.storage.hash_map_changed_listener import (
        HashMapChangedListener,
    )


class P2PService(
    SetupListener, MessageListener, ConnectionListener, RequestDataManager.Listener
):
    my_node_address: Optional["NodeAddress"] = None

    def __init__(
        self,
        network_node: "NetworkNode",
        peer_manager: "PeerManager",
        p2p_data_storage: "P2PDataStorage",
        request_data_manager: "RequestDataManager",
        peer_exchange_manager: "PeerExchangeManager",
        keep_alive_manager: "KeepAliveManager",
        broadcaster: "Broadcaster",
        socks5_proxy_provider: "Socks5ProxyProvider",
        encryption_service: "EncryptionService",
        key_ring: "KeyRing",
        mailbox_message_service: "MailboxMessageService",
    ):
        self.logger = get_ctx_logger(__name__)
        self._encryption_service = encryption_service
        self._key_ring = key_ring

        self._mailbox_message_service = mailbox_message_service

        self._network_node = network_node
        self._peer_manager = peer_manager

        self._broadcaster = broadcaster
        self._p2p_data_storage = p2p_data_storage
        self._request_data_manager = request_data_manager
        self._peer_exchange_manager = peer_exchange_manager

        self._network_ready_property: Optional[SimpleProperty] = None
        self._decrypted_direct_message_listeners = ThreadSafeSet[
            "DecryptedDirectMessageListener"
        ]()
        self._p2p_service_listeners = ThreadSafeSet["P2PServiceListener"]()
        self._shut_down_result_handlers = ThreadSafeSet[Callable[[], None]]()
        self._hidden_service_published_property = SimpleProperty(False)
        self._preliminary_data_received_property = SimpleProperty(False)
        self._num_connected_peers_property = SimpleProperty(0)

        self._is_bootstrapped = False
        self._keep_alive_manager = keep_alive_manager
        self._socks5_proxy_provider = socks5_proxy_provider

        self._subscriptions: list[Callable[[], None]] = []

        self._network_node.add_connection_listener(self)
        self._network_node.add_message_listener(self)
        self._request_data_manager.set_listener(self)

        #  We need to have both the initial data delivered and the hidden service published
        self._network_ready_property = combine_simple_properties(
            self._hidden_service_published_property,
            self._preliminary_data_received_property,
            transform=all,
        )
        self._network_ready_unsubscribe = self._network_ready_property.add_listener(
            lambda e: self.on_network_ready() if e.new_value else None
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    async def start(self, listener: Optional["P2PServiceListener"] = None):
        if listener is not None:
            self._subscriptions.append(
                self.add_p2p_service_listener(listener)
            )
        await self._network_node.start(self)

    def on_all_services_initialized(self):
        pass

    def shut_down(self, shut_down_complete_handler: Callable[[], None]):
        self.logger.info("P2PService shutdown started")
        self._shut_down_result_handlers.add(shut_down_complete_handler)

        # We need to make sure queued up messages are flushed out before we continue shut down other network services
        if self._broadcaster is not None:
            self._broadcaster.shut_down(self.do_shut_down)
        else:
            self.do_shut_down()

    def do_shut_down(self):
        self.logger.info("P2PService doShutDown started")
        if self._p2p_data_storage is not None:
            self._p2p_data_storage.shut_down()

        if self._peer_manager is not None:
            self._peer_manager.shut_down()

        if self._request_data_manager is not None:
            self._request_data_manager.shut_down()
            self._request_data_manager.set_listener(None)

        if self._peer_exchange_manager is not None:
            self._peer_exchange_manager.shut_down()

        if self._keep_alive_manager is not None:
            self._keep_alive_manager.shut_down()

        if self._network_ready_property is not None:
            self._network_ready_property.remove_all_listeners()
            self._network_ready_property = None

        for unsub in self._subscriptions:
            unsub()
        self._subscriptions.clear()

        if self._network_node is not None:
            self._network_node.remove_connection_listener(self)
            self._network_node.remove_message_listener(self)
            self._network_node.shut_down(
                lambda: [handler() for handler in self._shut_down_result_handlers]
            )
        else:
            for handler in self._shut_down_result_handlers:
                handler()
            self._shut_down_result_handlers.clear()

    #
    #  Startup sequence:
    #
    #  Variant 1 (normal expected mode):
    #  onTorNodeReady -> requestDataManager.firstDataRequestFromAnySeedNode()
    #  RequestDataManager.Listener.onDataReceived && onHiddenServicePublished -> onNetworkReady()
    #
    #  Variant 2 (no seed node available):
    #  onTorNodeReady -> requestDataManager.firstDataRequestFromAnySeedNode
    #  retry after 20-30 sec until we get at least one seed node connected
    #  RequestDataManager.Listener.onDataReceived && onHiddenServicePublished -> onNetworkReady()
    #

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // SetupListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_tor_node_ready(self):
        self._socks5_proxy_provider.set_socks5_proxy_internal(self._network_node)

        self._request_data_manager.request_preliminary_data()
        self._keep_alive_manager.start()
        for listener in self._p2p_service_listeners:
            listener.on_tor_node_ready()

    def on_hidden_service_published(self):
        check_argument(
            self._network_node.node_address_property.value is not None,
            "Address must be set when we have the hidden service ready",
        )

        self._hidden_service_published_property.set(True)

        for listener in self._p2p_service_listeners:
            listener.on_hidden_service_published()

    def on_setup_failed(self, error: Exception):
        for listener in self._p2p_service_listeners:
            listener.on_setup_failed(error)

    def on_request_custom_bridges(self):
        for listener in self._p2p_service_listeners:
            listener.on_request_custom_bridges()

    # Called from network_ready_property
    def on_network_ready(self):
        if self._network_ready_unsubscribe:
            self._network_ready_unsubscribe()
            self._network_ready_unsubscribe = None

        seed_node = (
            self._request_data_manager.get_node_address_of_preliminary_data_request()
        )
        check_argument(
            seed_node is not None,
            "seed_node_of_preliminary_data_request must be present",
        )

        self._request_data_manager.request_update_data()

        # If we start up first time we don't have any peers so we need to request from seed node.
        # As well it can be that the persisted peer list is outdated with dead peers.
        UserThread.run_after(
            lambda: self._peer_exchange_manager.request_reported_peers_from_seed_nodes(
                seed_node
            ),
            timedelta(milliseconds=100),
        )

        # If we have reported or persisted peers we try to connect to those
        UserThread.run_after(
            self._peer_exchange_manager.initial_request_peers_from_reported_or_persisted_peers,
            timedelta(milliseconds=300),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // RequestDataManager.Listener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_preliminary_data_received(self):
        check_argument(
            not self._preliminary_data_received_property.get(),
            "preliminary_data_received was already set before.",
        )
        self._preliminary_data_received_property.set(True)

    def on_updated_data_received(self):
        for listener in self._p2p_service_listeners:
            listener.on_updated_data_received()

    def on_no_seed_node_available(self):
        self._apply_is_bootstrapped(
            lambda listener: listener.on_no_seed_node_available()
        )

    def on_no_peers_available(self):
        for listener in self._p2p_service_listeners:
            listener.on_no_peers_available()

    def on_data_received(self):
        self._apply_is_bootstrapped(lambda listener: listener.on_data_received())

    def _apply_is_bootstrapped(
        self, listener_handler: Callable[["P2PServiceListener"], None]
    ):
        if not self._is_bootstrapped:
            self._is_bootstrapped = True

            self._p2p_data_storage.on_bootstrapped()

            # We don't use a listener at mailbox_message_service as we require the correct
            # order of execution. The mailbox_message_service must be called before.
            self._mailbox_message_service.on_bootstrapped()

            # Once we have applied the state in the P2P domain we notify our listeners
            for listener in self._p2p_service_listeners:
                listener_handler(listener)

            self._mailbox_message_service.init_after_bootstrapped()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // ConnectionListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_connection(self, connection: "Connection") -> None:
        self._num_connected_peers_property.set(
            len(self._network_node.get_all_connections())
        )
        # TODO check if still needed and why
        UserThread.run_after(
            lambda: self._num_connected_peers_property.set(
                len(self._network_node.get_all_connections())
            ),
            timedelta(seconds=3),
        )

    def on_disconnect(
        self, close_connection_reason: "CloseConnectionReason", connection: "Connection"
    ) -> None:
        self._num_connected_peers_property.set(
            len(self._network_node.get_all_connections())
        )
        # TODO check if still needed and why
        UserThread.run_after(
            lambda: self._num_connected_peers_property.set(
                len(self._network_node.get_all_connections())
            ),
            timedelta(seconds=3),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // MessageListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_message(
        self, network_envelope: "NetworkEnvelope", connection: "Connection"
    ) -> None:
        if isinstance(network_envelope, PrefixedSealedAndSignedMessage):
            sealed_msg = network_envelope
            try:
                decrypted_msg = self._encryption_service.decrypt_and_verify(
                    sealed_msg.sealed_and_signed
                )
                connection.maybe_handle_supported_capabilities_message(
                    decrypted_msg.network_envelope
                )

                node_address = connection.peers_node_address
                if node_address is not None:
                    for listener in self._decrypted_direct_message_listeners:
                        listener(decrypted_msg, node_address)
                else:
                    self.logger.error(
                        "peersNodeAddress is expected to be available at onMessage for "
                        "processing PrefixedSealedAndSignedMessage."
                    )

            except CryptoException as e:
                self.logger.warning(
                    "Decryption of a direct message failed. This is not expected as the "
                    "direct message was sent to our node."
                )
            except ProtobufferException as e:
                self.logger.error(
                    f"ProtobufferException at decryptAndVerify: {str(e)}", exc_info=e
                )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DirectMessages
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # TODO OfferAvailabilityResponse is called twice!
    def send_encrypted_direct_message(
        self,
        peer_node_address: "NodeAddress",
        pub_key_ring: "PubKeyRing",
        message: "NetworkEnvelope",
        send_direct_message_listener: "SendDirectMessageListener",
    ) -> None:
        assert (
            peer_node_address is not None
        ), "PeerAddress must not be null (send_encrypted_direct_message)"

        if self._is_bootstrapped:
            self.do_send_encrypted_direct_message(
                peer_node_address, pub_key_ring, message, send_direct_message_listener
            )
        else:
            raise NetworkNotReadyException()

    def do_send_encrypted_direct_message(
        self,
        peers_node_address: "NodeAddress",
        pub_key_ring: "PubKeyRing",
        message: "NetworkEnvelope",
        send_direct_message_listener: "SendDirectMessageListener",
    ) -> None:
        self.logger.debug(
            f"Send encrypted direct message {message.__class__.__name__} to peer {peers_node_address}"
        )

        assert (
            peers_node_address is not None
        ), "PeerAddress must not be null at do_send_encrypted_direct_message"
        assert (
            self._network_node.node_address_property.value is not None
        ), "My node address must not be null at do_send_encrypted_direct_message"

        if CapabilityUtils.capability_required_and_capability_not_supported(
            peers_node_address, message, self._peer_manager
        ):
            send_direct_message_listener.on_fault(
                "We did not send the EncryptedMessage "
                "because the peer does not support the capability."
            )
            return

        try:
            # Prefix is not needed for direct messages but as old code is doing the verification we still need to
            # send it if peer has not updated.
            sealed_msg = PrefixedSealedAndSignedMessage(
                sender_node_address=self._network_node.node_address_property.value,
                sealed_and_signed=self._encryption_service.encrypt_and_sign(
                    pub_key_ring, message
                ),
            )

            future = self._network_node.send_message(peers_node_address, sealed_msg)

            def on_success(r):
                send_direct_message_listener.on_arrived()

            def on_failure(e):
                self.logger.error(str(e), exc_info=e)
                send_direct_message_listener.on_fault(str(e))

            future.add_done_callback(
                FutureCallback(
                    on_success,
                    on_failure,
                )
            )

        except CryptoException as e:
            self.logger.error(str(message))
            self.logger.error(str(e), exc_info=e)
            send_direct_message_listener.on_fault(str(e))

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Data storage
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_persistable_network_payload(
        self, payload: "PersistableNetworkPayload", re_broadcast: bool
    ) -> bool:
        return self._p2p_data_storage.add_persistable_network_payload(
            payload, self._network_node.node_address_property.value, re_broadcast
        )

    def add_protected_storage_entry(
        self, protected_storage_payload: "ProtectedStoragePayload"
    ) -> bool:
        if self._is_bootstrapped:
            try:
                protected_storage_entry = (
                    self._p2p_data_storage.get_protected_storage_entry(
                        protected_storage_payload,
                        self._key_ring.signature_key_pair,
                    )
                )
                return self._p2p_data_storage.add_protected_storage_entry(
                    protected_storage_entry,
                    self._network_node.node_address_property.value,
                    None,
                )
            except CryptoException as e:
                self.logger.error(
                    "Signing at get_data_with_signed_seq_nr failed. That should never happen."
                )
                return False
        else:
            raise NetworkNotReadyException()

    def refresh_ttl(self, protected_storage_payload: "ProtectedStoragePayload") -> bool:
        if self._is_bootstrapped:
            try:
                refresh_ttl_message = self._p2p_data_storage.get_refresh_ttl_message(
                    protected_storage_payload, self._key_ring.signature_key_pair
                )
                return self._p2p_data_storage.refresh_ttl(
                    refresh_ttl_message, self._network_node.node_address_property.value
                )
            except CryptoException as e:
                self.logger.error(
                    "Signing at get_data_with_signed_seq_nr failed. That should never happen."
                )
                return False
        else:
            raise NetworkNotReadyException()

    def remove_data(self, protected_storage_payload: "ProtectedStoragePayload") -> bool:
        if self._is_bootstrapped:
            try:
                protected_storage_entry = (
                    self._p2p_data_storage.get_protected_storage_entry(
                        protected_storage_payload,
                        self._key_ring.signature_key_pair,
                    )
                )
                return self._p2p_data_storage.remove(
                    protected_storage_entry,
                    self._network_node.node_address_property.value,
                )
            except CryptoException as e:
                self.logger.error(
                    "Signing at get_data_with_signed_seq_nr failed. That should never happen."
                )
                return False
        else:
            raise NetworkNotReadyException()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Listeners
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_decrypted_direct_message_listener(
        self, listener: "DecryptedDirectMessageListener"
    ) -> None:
        self._decrypted_direct_message_listeners.add(listener)

    def remove_decrypted_direct_message_listener(
        self, listener: "DecryptedDirectMessageListener"
    ) -> None:
        self._decrypted_direct_message_listeners.discard(listener)

    def add_p2p_service_listener(self, listener: "P2PServiceListener"):
        self._p2p_service_listeners.add(listener)
        return lambda: self.remove_p2p_service_listener(listener)

    def remove_p2p_service_listener(self, listener: "P2PServiceListener") -> None:
        self._p2p_service_listeners.discard(listener)

    def add_hash_set_changed_listener(
        self, hash_map_changed_listener: "HashMapChangedListener"
    ) -> None:
        self._p2p_data_storage.add_hash_map_changed_listener(hash_map_changed_listener)
        return lambda: self.remove_hash_map_changed_listener(hash_map_changed_listener)

    def remove_hash_map_changed_listener(
        self, hash_map_changed_listener: "HashMapChangedListener"
    ) -> None:
        self._p2p_data_storage.remove_hash_map_changed_listener(
            hash_map_changed_listener
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getters
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @property
    def is_bootstrapped(self):
        return self._is_bootstrapped

    @property
    def network_node(self):
        return self._network_node

    @property
    def broadcaster(self):
        return self._broadcaster

    @property
    def mailbox_message_service(self):
        return self._mailbox_message_service

    @property
    def address(self):
        return self._network_node.node_address_property.get()

    @property
    def num_connected_peers(self):
        return self._num_connected_peers_property.get()

    @property
    def num_connected_peers_property(self):
        return self._num_connected_peers_property

    @property
    def data_map(self):
        return self._p2p_data_storage.map

    @property
    def p2p_data_storage(self):
        return self._p2p_data_storage

    @property
    def peer_manager(self):
        return self._peer_manager

    @property
    def key_ring(self):
        return self._key_ring

    def find_peers_capabilities(self, peer: "NodeAddress") -> Optional["Capabilities"]:
        for connection in self._network_node.get_confirmed_connections():
            if (
                connection.peers_node_address is not None
                and connection.peers_node_address == peer
            ):
                return connection.capabilities
        return None
