from collections.abc import Callable
from concurrent.futures import Future
from datetime import timedelta
from typing import TYPE_CHECKING, Optional
from bisq.common.capabilities import Capabilities
from bisq.common.crypto.crypto_exception import CryptoException
from bisq.common.crypto.pub_key_ring import PubKeyRing
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.common.protocol.protobuffer_exception import ProtobufferException
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.network.close_connection_reason import CloseConnectionReason
from bisq.core.network.p2p.network.connection import Connection
from bisq.core.network.p2p.network.connection_listener import ConnectionListener
from bisq.core.network.p2p.network.message_listener import MessageListener
from bisq.core.network.p2p.network.setup_listener import SetupListener
from bisq.core.network.p2p.network_not_ready_exception import NetworkNotReadyException
from bisq.core.network.p2p.peers.getdata.request_data_manager import RequestDataManager
from bisq.core.network.p2p.prefixed_sealed_and_signed_message import PrefixedSealedAndSignedMessage
from bisq.core.network.p2p.send_direct_message_listener import SendDirectMessageListener
from bisq.core.network.utils.capability_utils import CapabilityUtils
from utils.concurrency import ThreadSafeSet
from utils.data import SimpleProperty, SimplePropertyChangeEvent, combine_simple_properties

if TYPE_CHECKING:
    from bisq.core.network.p2p.storage.payload.persistable_network_payload import PersistableNetworkPayload
    from bisq.core.network.p2p.storage.payload.protected_storage_payload import ProtectedStoragePayload
    from bisq.core.network.socks5_proxy_provider import Socks5ProxyProvider
    from bisq.core.network.p2p.peers.broadcaster import Broadcaster
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.network.p2p.decrypted_direct_message_listener import DecryptedDirectMessageListener
    from bisq.core.network.p2p.peers.keepalive.keep_alive_manager import KeepAliveManager
    from bisq.core.network.p2p.storage.p2p_data_storage import P2PDataStorage
    from bisq.core.network.p2p.p2p_service_listener import P2PServiceListener
    from bisq.core.network.p2p.peers.peer_manager import PeerManager
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.crypto.encryption_service import EncryptionService
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.network.p2p.mailbox.mailbox_message_service import MailboxMessageService
    from bisq.core.network.p2p.peers.peerexchange.peer_exchange_manager import PeerExchangeManager
    from bisq.core.network.p2p.storage.hash_map_changed_listener import HashMapChangedListener

logger = get_logger(__name__)

class P2PService(SetupListener, MessageListener, ConnectionListener, RequestDataManager.Listener):
    my_node_address: Optional["NodeAddress"] = None
    
    @staticmethod
    def get_my_node_address():
        return P2PService.my_node_address
    
    def __init__(self, network_node: "NetworkNode", peer_manager: "PeerManager", p2p_data_storage: "P2PDataStorage", request_data_manager: "RequestDataManager",
                 peer_exchange_manager: "PeerExchangeManager", keep_alive_manager: "KeepAliveManager", broadcaster: "Broadcaster", socks5_proxy_provider: "Socks5ProxyProvider",
                 encryption_service: "EncryptionService", key_ring: "KeyRing", mailbox_message_service: "MailboxMessageService"):
        self.encryption_service = encryption_service
        self.key_ring = key_ring
        
        self.mailbox_message_service = mailbox_message_service
        
        self.network_node = network_node
        self.peer_manager = peer_manager
        
        self.broadcaster = broadcaster
        self.p2p_data_storage = p2p_data_storage
        self.request_data_manager = request_data_manager
        self.peer_exchange_manager = peer_exchange_manager
        
        self.network_ready = SimpleProperty(False)
        self.decrypted_direct_message_listeners: ThreadSafeSet["DecryptedDirectMessageListener"] = ThreadSafeSet()
        self.p2p_service_listeners: ThreadSafeSet["P2PServiceListener"] = ThreadSafeSet()
        self.shut_down_result_handlers: ThreadSafeSet["Callable"] = ThreadSafeSet()
        self.hidden_service_published = SimpleProperty(False)
        self.preliminary_data_received = SimpleProperty(False)
        self.num_connected_peers = SimpleProperty(0)
        
        self.is_bootstrapped = False
        self.keep_alive_manager = keep_alive_manager
        self.socks5_proxy_provider = socks5_proxy_provider
    
        self.network_node.add_connection_listener(self)
        self.network_node.add_message_listener(self)
        self.request_data_manager.set_listener(self)
        
        #  We need to have both the initial data delivered and the hidden service published
        self.network_ready_property = combine_simple_properties(self.hidden_service_published, self.preliminary_data_received, transform=all)
        self.network_ready_unsubscribe = self.network_ready_property.add_listener(lambda e: self.on_network_ready() if e.new_value else None)
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    async def start(self, listener: Optional["P2PServiceListener"] = None):
        if listener is not None:
            self.add_p2p_service_listener(listener)
        await self.network_node.start(self)

    def on_all_services_initialized(self):
        if self.network_node.node_address_property.value is not None:
            P2PService.my_node_address = self.network_node.node_address_property.value
        else:
            # If our HS is still not published
            def on_address_change(e: SimplePropertyChangeEvent["NodeAddress"]):
                if e.new_value is not None:
                    P2PService.my_node_address = self.network_node.node_address_property.value
            
            self.network_node.node_address_property.add_listener(on_address_change)

    def shut_down(self, shut_down_complete_handler: Callable):
        logger.info("P2PService shutdown started")
        self.shut_down_result_handlers.add(shut_down_complete_handler)

        # We need to make sure queued up messages are flushed out before we continue shut down other network services
        if self.broadcaster is not None:
            self.broadcaster.shut_down(self.do_shut_down)
        else:
            self.do_shut_down()

    def do_shut_down(self):
        logger.info("P2PService doShutDown started")
        if self.p2p_data_storage is not None:
            self.p2p_data_storage.shut_down()

        if self.peer_manager is not None:
            self.peer_manager.shut_down()

        if self.request_data_manager is not None:
            self.request_data_manager.shut_down()

        if self.peer_exchange_manager is not None:
            self.peer_exchange_manager.shut_down()

        if self.keep_alive_manager is not None:
            self.keep_alive_manager.shut_down()

        if self.network_ready_property.value is not None:
            self.network_ready_property.remove_all_listeners()

        if self.network_node is not None:
            self.network_node.shut_down(lambda: [handler() for handler in self.shut_down_result_handlers])
        else:
            for handler in self.shut_down_result_handlers:
                handler()


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
        self.socks5_proxy_provider.set_socks5_proxy_internal(self.network_node)
        
        self.request_data_manager.request_preliminary_data()
        self.keep_alive_manager.start()
        for listener in self.p2p_service_listeners:
            listener.on_tor_node_ready()

    def on_hidden_service_published(self):
        assert self.network_node.node_address_property.value is not None, "Address must be set when we have the hidden service ready"

        self.hidden_service_published.set(True)
        
        for listener in self.p2p_service_listeners:
            listener.on_hidden_service_published()

    def on_setup_failed(self, error: Exception):
        for listener in self.p2p_service_listeners:
            listener.on_setup_failed(error)

    def on_request_custom_bridges(self):
        for listener in self.p2p_service_listeners:
            listener.on_request_custom_bridges()

    # Called from network_ready_property
    def on_network_ready(self):
        if self.network_ready_unsubscribe:
            self.network_ready_unsubscribe()

        seed_node = self.request_data_manager.get_node_address_of_preliminary_data_request()
        assert seed_node is not None, "seed_node_of_preliminary_data_request must be present"

        self.request_data_manager.request_update_data()

        # If we start up first time we don't have any peers so we need to request from seed node.
        # As well it can be that the persisted peer list is outdated with dead peers.
        UserThread.run_after(lambda: self.peer_exchange_manager.request_reported_peers_from_seed_nodes(seed_node), timedelta(milliseconds=100))
        
        # If we have reported or persisted peers we try to connect to those
        UserThread.run_after(self.peer_exchange_manager.initial_request_peers_from_reported_or_persisted_peers, timedelta(milliseconds=300))        

    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // RequestDataManager.Listener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_preliminary_data_received(self):
        assert not self.preliminary_data_received.get(), "preliminary_data_received was already set before."
        self.preliminary_data_received.set(True)

    def on_updated_data_received(self):
        for listener in self.p2p_service_listeners:
            listener.on_updated_data_received()

    def on_no_seed_node_available(self):
        self._apply_is_bootstrapped(lambda listener: listener.on_no_seed_node_available())

    def on_no_peers_available(self):
        for listener in self.p2p_service_listeners:
            listener.on_no_peers_available()

    def on_data_received(self):
        self._apply_is_bootstrapped(lambda listener: listener.on_data_received())

    def _apply_is_bootstrapped(self, listener_handler: Callable[["P2PServiceListener"], None]):
        if not self.is_bootstrapped:
            self.is_bootstrapped = True

            self.p2p_data_storage.on_bootstrapped()

            # We don't use a listener at mailbox_message_service as we require the correct
            # order of execution. The mailbox_message_service must be called before.
            self.mailbox_message_service.on_bootstrapped()

            # Once we have applied the state in the P2P domain we notify our listeners
            for listener in self.p2p_service_listeners:
                listener_handler(listener)

            self.mailbox_message_service.init_after_bootstrapped()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // ConnectionListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_connection(self, connection: "Connection") -> None:
        self.num_connected_peers.set(len(self.network_node.get_all_connections()))
        # TODO check if still needed and why
        UserThread.run_after(
            lambda: self.num_connected_peers.set(len(self.network_node.get_all_connections())), 
            timedelta(seconds=3)
        )

    def on_disconnect(self, close_connection_reason: "CloseConnectionReason", connection: "Connection") -> None:
        self.num_connected_peers.set(len(self.network_node.get_all_connections()))
        # TODO check if still needed and why
        UserThread.run_after(
            lambda: self.num_connected_peers.set(len(self.network_node.get_all_connections())), 
            timedelta(seconds=3)
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // MessageListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_message(self, network_envelope: "NetworkEnvelope", connection: "Connection") -> None:
        if isinstance(network_envelope, PrefixedSealedAndSignedMessage):
            sealed_msg = network_envelope
            try:
                decrypted_msg = self.encryption_service.decrypt_and_verify(sealed_msg.sealed_and_signed)
                connection.maybe_handle_supported_capabilities_message(decrypted_msg.network_envelope)
                
                node_address = connection.peers_node_address
                if node_address is not None:
                    for listener in self.decrypted_direct_message_listeners:
                        listener(decrypted_msg, node_address)
                else:
                    logger.error("peersNodeAddress is expected to be available at onMessage for "
                               "processing PrefixedSealedAndSignedMessage.")
                    
            except CryptoException as e:
                logger.warning("Decryption of a direct message failed. This is not expected as the "
                             "direct message was sent to our node.")
            except ProtobufferException as e:
                logger.error(f"ProtobufferException at decryptAndVerify: {str(e)}", exc_info=e)


    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DirectMessages
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # TODO OfferAvailabilityResponse is called twice!
    def send_encrypted_direct_message(self, peer_node_address: "NodeAddress", pub_key_ring: "PubKeyRing", 
                                    message: "NetworkEnvelope", send_direct_message_listener: "SendDirectMessageListener") -> None:
        assert peer_node_address is not None, "PeerAddress must not be null (send_encrypted_direct_message)"

        if self.is_bootstrapped:
            self.do_send_encrypted_direct_message(peer_node_address, pub_key_ring, message, send_direct_message_listener)
        else:
            raise NetworkNotReadyException()

    def do_send_encrypted_direct_message(self, peers_node_address: "NodeAddress", pub_key_ring: "PubKeyRing",
                                       message: "NetworkEnvelope", send_direct_message_listener: "SendDirectMessageListener") -> None:
        logger.debug(f"Send encrypted direct message {message.__class__.__name__} to peer {peers_node_address}")

        assert peers_node_address is not None, "PeerAddress must not be null at do_send_encrypted_direct_message"
        assert self.network_node.node_address_property.value is None, "My node address must not be null at do_send_encrypted_direct_message"

        if CapabilityUtils.capability_required_and_capability_not_supported(peers_node_address, message, self.peer_manager):
            send_direct_message_listener.on_fault("We did not send the EncryptedMessage "
                                                  "because the peer does not support the capability.")
            return

        try:
            # Prefix is not needed for direct messages but as old code is doing the verification we still need to
            # send it if peer has not updated.
            sealed_msg = PrefixedSealedAndSignedMessage(
                sender_node_address=self.network_node.node_address_property.value,
                sealed_and_signed=self.encryption_service.encrypt_and_sign(pub_key_ring, message),
            )
                
            def on_done(future: Future):
                try: 
                    future.result()
                    send_direct_message_listener.on_arrived()
                except Exception as e:
                    logger.error(str(e), exc_info=e)
                    send_direct_message_listener.on_fault(str(e))

            future = self.network_node.send_message(peers_node_address, sealed_msg)
            future.add_done_callback(on_done)

        except CryptoException as e:
            logger.error(str(message))
            logger.error(str(e), exc_info=e)
            send_direct_message_listener.on_fault(str(e))

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Data storage
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_persistable_network_payload(self, payload: "PersistableNetworkPayload", re_broadcast: bool) -> bool:
        return self.p2p_data_storage.add_persistable_network_payload(
            payload, 
            self.network_node.node_address_property.value,
            re_broadcast
        )

    def add_protected_storage_entry(self, protected_storage_payload: "ProtectedStoragePayload") -> bool:
        if self.is_bootstrapped:
            try:
                protected_storage_entry = self.p2p_data_storage.get_protected_storage_entry(
                    protected_storage_payload,
                    self.key_ring.signature_key_pair,
                )
                return self.p2p_data_storage.add_protected_storage_entry(
                    protected_storage_entry,
                    self.network_node.node_address_property.value,
                    None
                )
            except CryptoException as e:
                logger.error("Signing at get_data_with_signed_seq_nr failed. That should never happen.")
                return False
        else:
            raise NetworkNotReadyException()

    def refresh_ttl(self, protected_storage_payload: "ProtectedStoragePayload") -> bool:
        if self.is_bootstrapped:
            try:
                refresh_ttl_message = self.p2p_data_storage.get_refresh_ttl_message(
                    protected_storage_payload,
                    self.key_ring.signature_key_pair
                )
                return self.p2p_data_storage.refresh_ttl(
                    refresh_ttl_message,
                    self.network_node.node_address_property.value
                )
            except CryptoException as e:
                logger.error("Signing at get_data_with_signed_seq_nr failed. That should never happen.")
                return False
        else:
            raise NetworkNotReadyException()

    def remove_data(self, protected_storage_payload: "ProtectedStoragePayload") -> bool:
        if self.is_bootstrapped:
            try:
                protected_storage_entry = self.p2p_data_storage.get_protected_storage_entry(
                    protected_storage_payload,
                    self.key_ring.signature_key_pair,
                )
                return self.p2p_data_storage.remove(
                    protected_storage_entry,
                    self.network_node.node_address_property.value
                )
            except CryptoException as e:
                logger.error("Signing at get_data_with_signed_seq_nr failed. That should never happen.")
                return False
        else:
            raise NetworkNotReadyException()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Listeners
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_decrypted_direct_message_listener(self, listener: "DecryptedDirectMessageListener") -> None:
        self.decrypted_direct_message_listeners.add(listener)

    def remove_decrypted_direct_message_listener(self, listener: "DecryptedDirectMessageListener") -> None:
        self.decrypted_direct_message_listeners.discard(listener)

    def add_p2p_service_listener(self, listener: "P2PServiceListener") -> None:
        self.p2p_service_listeners.add(listener)

    def remove_p2p_service_listener(self, listener: "P2PServiceListener") -> None:
        self.p2p_service_listeners.discard(listener)

    def add_hash_set_changed_listener(self, hash_map_changed_listener: "HashMapChangedListener") -> None:
        self.p2p_data_storage.add_hash_map_changed_listener(hash_map_changed_listener)

    def remove_hash_map_changed_listener(self, hash_map_changed_listener: "HashMapChangedListener") -> None:
        self.p2p_data_storage.remove_hash_map_changed_listener(hash_map_changed_listener)

    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getters
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    
    def get_network_node(self):
        return self.network_node

    def get_address(self):
        return self.network_node.node_address_property.value

    def get_num_connected_peers(self):
        return self.num_connected_peers

    def get_data_map(self):
        return self.p2p_data_storage.map

    def get_p2p_data_storage(self):
        return self.p2p_data_storage

    def get_peer_manager(self):
        return self.peer_manager

    def get_key_ring(self):
        return self.key_ring

    def find_peers_capabilities(self, peer: "NodeAddress") -> Optional["Capabilities"]:
        for connection in self.network_node.get_confirmed_connections():
            if (connection.peers_node_address is not None and 
                connection.peers_node_address == peer):
                return connection.capabilities
        return None