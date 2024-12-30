import concurrent.futures
from io import BufferedReader
import socket as Socket
import threading
import time
import uuid
from typing import TYPE_CHECKING, Optional
from collections.abc import Callable
from bisq.common.protocol.protobuffer_exception import ProtobufferException
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.network.p2p.extended_data_size_permission import ExtendedDataSizePermission
from bisq.core.network.p2p.peers.keepalive.messages.keep_alive_message import KeepAliveMessage
from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray
import proto.pb_pb2 as protobuf
from proto.delimited_protobuf import read_delimited
import bisq.common.version as Version
from google.protobuf.message import Error as InvalidProtocolBufferException  

import concurrent

from bisq.common.capabilities import Capabilities
from bisq.common.config.config import Config
from bisq.common.has_capabilities import HasCapabilities
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.bundle_of_envelopes import BundleOfEnvelopes
from bisq.core.network.p2p.close_connection_message import CloseConnectionMessage
from bisq.core.network.p2p.network.ban_filter import BanFilter
from bisq.core.network.p2p.network.close_connection_reason import CloseConnectionReason
from bisq.core.network.p2p.network.connection_state import ConnectionState
from bisq.core.network.p2p.network.connection_statistics import ConnectionStatistics
from bisq.core.network.p2p.network.rule_violation import RuleViolation
from bisq.core.network.p2p.network.statistic import Statistic
from bisq.core.network.p2p.network.supported_capabilities_listener import SupportedCapabilitiesListener
from bisq.core.network.p2p.storage.messages.add_data_message import AddDataMessage
from bisq.core.network.p2p.storage.messages.add_persistable_network_payload_message import AddPersistableNetworkPayloadMessage
from bisq.core.network.p2p.storage.messages.remove_data_message import RemoveDataMessage
from bisq.core.network.p2p.supported_capabilities_message import SupportedCapabilitiesMessage
from bisq.core.network.p2p.senders_node_address_message import SendersNodeAddressMessage
from bisq.core.network.p2p.network.message_listener import MessageListener
from bisq.core.network.p2p.network.proto_output_stream import ProtoOutputStream
from bisq.common.setup.log_setup import get_logger
from utils.concurrency import ThreadSafeDict, ThreadSafeSet, ThreadSafeWeakSet
from utils.formatting import to_truncated_string
from utils.time import get_time_ms
from bisq.core.network.p2p.storage.payload.capability_requiring_payload import CapabilityRequiringPayload

if TYPE_CHECKING:
    from bisq.core.network.p2p.network.connection_listener import ConnectionListener
    from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.common.proto import Proto

logger = get_logger(__name__)

class Connection(HasCapabilities, Callable[[], None], MessageListener):
    """
    Connection is created by the server thread or by send_message from NetworkNode.
    """

    PERMITTED_MESSAGE_SIZE = 200 * 1024  # 200 kb
    MAX_PERMITTED_MESSAGE_SIZE = 10 * 1024 * 1024  # 10 MB (425 offers resulted in about 660 kb, mailbox msg will add more to it) offer has usually 2 kb, mailbox 3kb.
    # JAVA TODO decrease limits again after testing
    SOCKET_TIMEOUT_SEC = 240
    SHUTDOWN_TIMEOUT_SEC = 0.1
    _config: Config = None
    
    @property
    def config(self):
        if Connection._config is None:
            from global_container import GLOBAL_CONTAINER
            Connection._config = GLOBAL_CONTAINER.config
        return Connection._config

    def __init__(self, socket: Socket.socket, message_listener: MessageListener,
                connection_listener: 'ConnectionListener',
                network_proto_resolver: 'NetworkProtoResolver',
                peers_node_address: Optional['NodeAddress'] = None,
                ban_filter: Optional[BanFilter] = None):
        self.last_send_timestamp = 0
        self.last_read_timestamp = 0
        self.message_listeners: ThreadSafeSet[MessageListener] = ThreadSafeSet()
        self.stopped = False
        self.thread_name_set = False
        # We use a weak reference here to ensure that no connection causes a memory leak in case it get closed without
        # the shutDown being called.
        self.capabilities_listeners: ThreadSafeWeakSet[SupportedCapabilitiesListener] = ThreadSafeWeakSet()
        self.rule_violations: ThreadSafeDict[RuleViolation, int] = ThreadSafeDict()
        self.rule_violation: RuleViolation = None
        self.capabilities = Capabilities()
        self.message_time_stamps: list[int] = []

        self.socket = socket
        self.connection_listener = connection_listener
        self.ban_filter = ban_filter

        self.uid = str(uuid.uuid4())
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="Executor service for connection with uid " + self.uid)

        self.statistic = Statistic()
        
        self.add_message_listener(message_listener)

        self.network_proto_resolver = network_proto_resolver
        self.connection_state = ConnectionState(self)
        self.connection_statistics = ConnectionStatistics(self, self.connection_state)
        self.peers_node_address: Optional["NodeAddress"] = None
        self.proto_output_stream: Optional["ProtoOutputStream"] = None
        self.proto_input_stream: Optional["BufferedReader"] = None
        self.init(peers_node_address)

    def init(self, peers_node_address: Optional['NodeAddress']):
        try:
            self.socket.settimeout(Connection.SOCKET_TIMEOUT_SEC)
            
            self.proto_output_stream = ProtoOutputStream(self.socket.makefile('wb'), self.statistic)
            self.proto_input_stream = self.socket.makefile('rb')

            # We create a thread for handling inputStream data
            self.executor.submit(self.run)

            if peers_node_address is not None:
                self.set_peers_node_address(peers_node_address)
                if self.ban_filter and self.ban_filter.is_peer_banned(peers_node_address):
                    logger.warning("We created an outbound connection with a banned peer")
                    self.report_invalid_request(RuleViolation.PEER_BANNED)
            UserThread.execute(lambda: self.connection_listener.on_connection(self))
        except Exception as e:
            self.handle_exception(e)

    def send_message(self, network_envelope: NetworkEnvelope):
        ts = get_time_ms()
        logger.debug(f">> Send networkEnvelope of type: {network_envelope.__class__.__name__}")

        if self.stopped:
            logger.debug("called sendMessage but was already stopped")
            return
        
        if self.ban_filter and self.peers_node_address and self.ban_filter.is_peer_banned(self.peers_node_address):
            logger.warning(f"We tried to send a message to a banned peer. message={network_envelope.__class__.__name__}")
            self.report_invalid_request(RuleViolation.PEER_BANNED)
            return
        
        if not self.test_capability(network_envelope):
            logger.debug("Capability for networkEnvelope is required but not supported")
            return

        network_envelope_size = network_envelope.to_proto_network_envelope().ByteSize()
        try:
            now = get_time_ms()
            elapsed = now - self.last_send_timestamp
            if elapsed < self.get_send_msg_throttle_trigger():
                logger.debug(f"We got 2 sendMessage requests in less than {self.get_send_msg_throttle_trigger()} ms. We set the thread to sleep for {self.get_send_msg_throttle_sleep()} ms to avoid flooding our peer. lastSendTimeStamp={self.last_send_timestamp}, now={now}, elapsed={elapsed}, networkEnvelope={network_envelope.__class__.__name__}")
                time.sleep(self.get_send_msg_throttle_sleep())
            self.last_send_timestamp = now
            if not self.stopped:
                self.proto_output_stream.write_envelope(network_envelope)
                UserThread.execute(lambda: list(map(lambda e: e.on_message_sent(network_envelope, self), self.message_listeners)))
                UserThread.execute(lambda: self.connection_statistics.add_send_msg_metrics(get_time_ms() - ts, network_envelope_size))
        except Exception as t:
            self.handle_exception(t)
            raise RuntimeError(t) from t
        
    def test_capability(self, network_envelope: 'NetworkEnvelope' = None, capability_requiring_payload: 'CapabilityRequiringPayload' = None) -> bool:
        if capability_requiring_payload is not None:
            result = self.capabilities.contains_all(capability_requiring_payload.get_required_capabilities()) 
            if not result:
                logger.debug(f"We did not send {capability_requiring_payload.__class__.__name__} because capabilities are not supported.")
            return result
        elif network_envelope is not None:
            if isinstance(network_envelope, BundleOfEnvelopes):
                self.update_bundle_of_envelopes(network_envelope)
                # If the bundle is empty we dont send the networkEnvelope
                return network_envelope.envelopes != []
            else:
                capability_requiring_payload = self.extract_capability_requiring_payload(network_envelope)
                if capability_requiring_payload:
                    return self.test_capability(capability_requiring_payload=capability_requiring_payload)
                else:
                    return True
        else:
            return False

    def update_bundle_of_envelopes(self, bundle_of_envelopes: 'BundleOfEnvelopes'):
        for network_envelope in bundle_of_envelopes.envelopes:
            if not self.test_capability(network_envelope=network_envelope):
                bundle_of_envelopes.envelopes.remove(network_envelope)

    def extract_capability_requiring_payload(self, proto: 'Proto'):
        candidate = proto
        # Lets check if our networkEnvelope is a wrapped data structure
        if isinstance(proto, AddDataMessage):
            candidate = proto.protected_storage_entry.protected_storage_payload
        elif isinstance(proto, RemoveDataMessage):
            candidate = proto.protected_storage_entry.protected_storage_payload
        elif isinstance(proto, AddPersistableNetworkPayloadMessage):
            candidate = proto.persistable_network_payload

        if isinstance(candidate, CapabilityRequiringPayload):
            return candidate
        else:
            return None

    def add_message_listener(self, listener):
        self.message_listeners.add(listener)

    def remove_message_listener(self, listener):
        self.message_listeners.discard(listener)

    def add_weak_capabilities_listener(self, listener):
        self.capabilities_listeners.add(listener)

    def violates_throttle_limit(self):
        now = get_time_ms()

        self.message_time_stamps.append(now)

        # clean list
        while len(self.message_time_stamps) > self.get_msg_throttle_per_10_sec():
            self.message_time_stamps.pop(0)

        return (self._violates_throttle_limit(now, 1, self.get_msg_throttle_per_sec()) or
                self._violates_throttle_limit(now, 10, self.get_msg_throttle_per_10_sec()))

    def get_msg_throttle_per_sec(self):
        if self.config:
            return self.config.msg_throttle_per_sec
        else:
            return 200
    
    def get_msg_throttle_per_10_sec(self):
        if self.config:
            return self.config.msg_throttle_per_10_sec
        else:
            return 1000

    def get_send_msg_throttle_sleep(self):
        if self.config:
            return self.config.send_msg_throttle_sleep
        else:
            return 50

    def get_send_msg_throttle_trigger(self):
        if self.config:
            return self.config.send_msg_throttle_trigger
        else:
            return 20

    def _violates_throttle_limit(self, now: int, seconds: int, message_count_limit: int) -> bool:
        if len(self.message_time_stamps) >= message_count_limit:
            # find the entry in the message timestamp history which determines whether we overshot the limit or not
            compare_value = self.message_time_stamps[len(self.message_time_stamps) - message_count_limit]
            #  if duration < seconds sec we received too much network_messages
            if (now - compare_value < seconds * 1000):
                logger.error(f"violatesThrottleLimit {message_count_limit}/{seconds} second(s)")
                return True
        return False
    
    ####################################
    ## MessageListener implementation ##
    ####################################

    def on_message(self, network_envelope: 'NetworkEnvelope', connection: 'Connection'):
        if connection != self:
            raise RuntimeError("unexpected different connection was passed to on_message")
        
        if isinstance(network_envelope, BundleOfEnvelopes):
            self.on_bundle_of_envelopes(network_envelope, connection)
        else:
            UserThread.execute(lambda: list(map(lambda e: e.on_message(network_envelope, connection), self.message_listeners)))

    def on_message_sent(self, network_envelope, connection):
        pass

    def on_bundle_of_envelopes(self, bundle_of_envelopes: 'BundleOfEnvelopes', connection: 'Connection'):
        items_by_hash: dict["StorageByteArray", set['NetworkEnvelope']] = {}
        envelopes_to_process: set[NetworkEnvelope] = set()
        network_envelopes = bundle_of_envelopes.envelopes
        for network_envelope in network_envelopes:
            if isinstance(network_envelope, SendersNodeAddressMessage):
                is_valid = self.process_senders_node_address_message(network_envelope)
                if not is_valid:
                    logger.warning(f"Received an invalid {network_envelope.__class__.__name__} at processing BundleOfEnvelopes")
                    continue
            if isinstance(network_envelope, AddPersistableNetworkPayloadMessage):
                persistable_network_payload = network_envelope.persistable_network_payload
                hash_value = persistable_network_payload.get_hash()
                item_name = persistable_network_payload.__class__.__name__
                byte_array = StorageByteArray(hash_value)
                items_by_hash[byte_array] = items_by_hash.setdefault(byte_array, set())
                envelopes_by_hash = items_by_hash[byte_array]
                if not network_envelope in envelopes_by_hash:
                    envelopes_by_hash.add(network_envelope)
                    envelopes_to_process.add(network_envelope)
                else:
                    logger.debug(f"We got duplicated items for {item_name}. We ignore the duplicates. Hash: {bytes_as_hex_string(hash_value)}")
            else:
                envelopes_to_process.add(network_envelope)

        list(map(lambda envelope: UserThread.execute(lambda: list(map(lambda listener: listener.on_message(envelope, connection), self.message_listeners))), envelopes_to_process))

    ####################################

    def set_peers_node_address(self, peerNodeAddress: 'NodeAddress'):
        assert peerNodeAddress, "peerNodeAddress must not be None"
        self.peers_node_address = peerNodeAddress
        from bisq.core.network.p2p.network.inbound_connection import InboundConnection
        if isinstance(self, InboundConnection):
            logger.debug("\n\n############################################################\n" +
                         "We got the peers node address set.\n" +
                         f"peersNodeAddress= {peerNodeAddress.get_full_address()}\n" +
                         f"connection.uid= {self.uid}\n" +
                         "############################################################\n")
    
    def handle_shut_down(self, close_connection_reason: CloseConnectionReason, shut_down_complete_handler: Optional[Callable[[], None]] = None):
        try:
            reason = self.rule_violation.name if close_connection_reason == CloseConnectionReason.RULE_VIOLATION else close_connection_reason.name
            self.send_message(CloseConnectionMessage(reason))

            self.stopped = True

            time.sleep(0.2)
        except Exception as e:
            logger.error(e, exc_info=e)
        finally:
            self.stopped = True
            UserThread.execute(lambda: self.do_shut_down(close_connection_reason, shut_down_complete_handler))
 
    
    def shut_down(self, close_connection_reason: CloseConnectionReason, shut_down_complete_handler: Optional[Callable[[], None]] = None):
        logger.debug(f"shutDown: peersNodeAddressOptional={self.peers_node_address}, closeConnectionReason={close_connection_reason}")
        self.connection_state.shut_down()
        if not self.stopped:
            peers_node_address = str(self.peers_node_address) if self.peers_node_address else "None"
            logger.debug(
                f"\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
                f"ShutDown connection:"
                f"\npeersNodeAddress={peers_node_address}"
                f"\ncloseConnectionReason={close_connection_reason}"
                f"\nuid={self.uid}"
                f"\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
            )
            if close_connection_reason.send_close_message:
                threading.Thread(target=lambda: self.handle_shut_down(close_connection_reason, shut_down_complete_handler), name=f"Connection:SendCloseConnectionMessage-{self.uid}").start()
            else:
                self.stopped = True
                self.do_shut_down(close_connection_reason, shut_down_complete_handler)
        else:
            logger.debug("stopped was already at shutDown call")
            UserThread.execute(lambda: self.do_shut_down(close_connection_reason, shut_down_complete_handler))

    def do_shut_down(self, close_connection_reason: CloseConnectionReason, shut_down_complete_handler: Optional[Callable[[], None]] = None):
        # Use UserThread.execute as it's not clear if that is called from a non-UserThread
        UserThread.execute(lambda: self.connection_listener.on_disconnect(close_connection_reason, self))
        try:
            self.proto_output_stream.on_connection_shutdown()
            self.socket.close()
        except Socket.error as e:
            logger.trace(f"SocketException at shutdown might be expected. {e}")
        except Exception as e:
            logger.error(f"Exception at shutdown. {e}")
        finally:
            self.capabilities_listeners.clear()
            try:
                self.proto_input_stream.close()
            except Exception as e:
                logger.error(str(e))
            self.executor.shutdown(wait=True, cancel_futures=True)
            logger.debug(f"Connection shutdown complete {self}")

            #  Use UserThread.execute as it's not clear if that is called from a non-UserThread
            if shut_down_complete_handler is not None:
                UserThread.execute(shut_down_complete_handler)

    def __call__(self, *args, **kwargs):
        self.run()

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, Connection):
            return False
        return self.uid == other.uid

    def __hash__(self) -> int:
        return hash(self.uid)

    def __str__(self) -> str:
        from bisq.core.network.p2p.network.inbound_connection import InboundConnection
        connection_type = "InboundConnection" if isinstance(self, InboundConnection) else "OutboundConnection"
        return (f"Connection{{"
            f"peerAddress={self.peers_node_address}, "
            f"connectionState={self.connection_state}, "
            f"connectionType={connection_type}, "
            f"uid='{self.uid}'}}")

    def print_details(self) -> str:
        """
        Returns a string with detailed information about the connection.
        """
        try:
            local_port = self.socket.getsockname()[1]
            remote_port = self.socket.getpeername()[1]
            port_info = f"localPort={local_port}/port={remote_port}"
        except Exception as e:
            port_info = f"port=Unknown due to error: {e}"

        return (f"Connection(peerAddress={self.peers_node_address}, "
                f"connectionState={self.connection_state}, portInfo={port_info}, "
                f"uid='{self.uid}', ruleViolation={self.rule_violation}, "
                f"ruleViolations={self.rule_violations}, "
                f"supportedCapabilities={self.capabilities}, stopped={self.stopped})")

    ####################################
    ## Shared space
    ####################################

    # Holds all shared data between Connection and InputHandler
    # Runs in same thread as Connection

    def report_invalid_request(self, rule_violation: 'RuleViolation'):
        logger.info(f"We got reported the ruleViolation {rule_violation.name} at connection with address {self.peers_node_address} and uid {self.uid}")
        num_rule_violations = self.rule_violations.get(rule_violation, 0) + 1
        self.rule_violations.put(rule_violation, num_rule_violations) 

        if num_rule_violations >= rule_violation.max_tolerance:
            logger.warning(f"We close connection as we received too many corrupt requests. ruleViolations={self.rule_violations} connection with address{self.peers_node_address} and uid {self.uid}")
            self.rule_violation = rule_violation
            if rule_violation == RuleViolation.PEER_BANNED:
                logger.debug(f"We close connection due RuleViolation.PEER_BANNED. peersNodeAddress={self.peers_node_address}")
                self.shut_down(CloseConnectionReason.PEER_BANNED)
            elif rule_violation == RuleViolation.INVALID_CLASS:
                logger.warning("We close connection due RuleViolation.INVALID_CLASS")
                self.shut_down(CloseConnectionReason.INVALID_CLASS_RECEIVED)
            else:
                logger.warning("We close connection due RuleViolation.RULE_VIOLATION")
                self.shut_down(CloseConnectionReason.RULE_VIOLATION)
            return True
        else:
            return False


    def handle_exception(self, exception: Exception):
        if self.stopped:
            return
        
        close_connection_reason = CloseConnectionReason.UNKNOWN_EXCEPTION
        if isinstance(exception, Socket.timeout):
            close_connection_reason = CloseConnectionReason.SOCKET_TIMEOUT
            logger.info(f"Shut down caused by exception {repr(exception)} on connection={self}")
        elif isinstance(exception, EOFError):
            close_connection_reason = CloseConnectionReason.TERMINATED
            logger.warning(f"Shut down caused by exception {repr(exception)} on connection={self}")
        elif isinstance(exception, (Socket.herror, Socket.gaierror, Socket.error)):
            if self.socket._closed:
                close_connection_reason = CloseConnectionReason.SOCKET_CLOSED
            else:
                close_connection_reason = CloseConnectionReason.RESET
            logger.info(f"SocketException (expected if connection lost). closeConnectionReason={close_connection_reason}; connection={self}")
        elif isinstance(exception, (ValueError,)):
            close_connection_reason =  CloseConnectionReason.CORRUPTED_DATA
            logger.warning(f"Shut down caused by exception {repr(exception)} on connection={self}")
        else:
            logger.warning(f"Unknown exception at socket: {self.socket}, peer={self.peers_node_address}, Exception={exception}")
        
        self.shut_down(close_connection_reason)        
    

    def process_senders_node_address_message(self, senders_node_address_message: SendersNodeAddressMessage) -> bool:
        sender_node_address = senders_node_address_message.sender_node_address
        assert sender_node_address, "sender_node_address must not be None at SendersNodeAddressMessage"
        
        if self.peers_node_address:
            if self.peers_node_address != sender_node_address:
                raise ValueError(f"sender_node_address not matching connection's peer address.\n\t message={senders_node_address_message}")
        else:
            self.set_peers_node_address(sender_node_address)

        if self.ban_filter and self.ban_filter.is_peer_banned(sender_node_address):
            logger.warning("Sender is banned. Shutting down connection.")
            self.report_invalid_request(RuleViolation.PEER_BANNED)
            return False

        return True

    def run(self):
        try:
            threading.current_thread().name = f"InputHandler-{to_truncated_string(self.uid, 15)}"
            while not self.stopped and threading.current_thread().is_alive():
                if  not self.thread_name_set and self.peers_node_address:
                    threading.current_thread().name = f"InputHandler-{to_truncated_string(self.peers_node_address.get_full_address(), 15)}"
                    self.thread_name_set = True

                if self.socket is not None and self.socket._closed:
                    logger.warning(f'Socket is None or closed socket={self.socket}')
                    self.shut_down(CloseConnectionReason.SOCKET_CLOSED)
                    return
                try:
                    # Blocking read from the inputStream
                    proto = read_delimited(self.proto_input_stream, protobuf.NetworkEnvelope)
                    ts = get_time_ms()
                    
                    if self.socket is not None and self.socket._closed:
                        logger.warning(f'Socket is None or closed socket={self.socket}')
                        self.shut_down(CloseConnectionReason.SOCKET_CLOSED)
                        return
                    
                    if proto is None:
                        if self.stopped:
                            return
                        data = self.proto_input_stream.read()
                        if  data == bytes():
                            logger.warning("proto is None because EOF was read. That is expected if client got stopped without proper shutdown.")
                        else:
                            logger.warning("proto is None. protoInputStream.read()=" + data.hex())
                        self.shut_down(CloseConnectionReason.NO_PROTO_BUFFER_ENV)
                        return
                    
                    if self.ban_filter and self.peers_node_address and self.ban_filter.is_peer_banned(self.peers_node_address):
                        logger.warning(f"We got a message from a banned peer. proto={str(proto)}")
                        self.report_invalid_request(RuleViolation.PEER_BANNED)
                        return

                except Socket.error as e:
                    logger.warning(f"Socket error: {e}")
                    break
                except EOFError:
                    logger.warning("EOF Error")
                    break

                if not proto:
                    continue



                now = get_time_ms()
                elapsed = now - self.last_read_timestamp
                if elapsed < 10:
                    logger.debug(f"We got 2 network messages received in less than 10 ms. We set the thread to sleep "
                                 f"for 20 ms to avoid getting flooded by our peer. lastReadTimeStamp={self.last_read_timestamp}, now={now}, elapsed={elapsed}")
                    time.sleep(20)

                try:
                    # NOTE: this is needed to not report violations for things we do not support like DAO stuff
                    network_envelope = self.network_proto_resolver.from_proto(proto)
                except ProtobufferException as e:
                    if "Unknown proto message case" in str(e):
                        logger.debug(f"Unsupported proto message. This is probably expected. original error={e}")
                        return
                    else:
                        raise
                
                self.last_read_timestamp = now
                logger.debug(f"<< Received networkEnvelope of type: {type(network_envelope).__name__}")
                size = proto.ByteSize()

                # We want to track the size of each object even if it is invalid data
                self.statistic.add_received_bytes(size)

                # We want to track the network_messages also before the checks, so do it early...
                self.statistic.add_received_message(network_envelope)
                
                # First we check the size
                exceeds = False
                if isinstance(network_envelope, ExtendedDataSizePermission):
                    exceeds = size >  Connection.MAX_PERMITTED_MESSAGE_SIZE
                else:
                    exceeds = size > Connection.PERMITTED_MESSAGE_SIZE

                if isinstance(network_envelope, AddPersistableNetworkPayloadMessage) and not network_envelope.persistable_network_payload.verify_hash_size():
                    logger.warning(f"PersistableNetworkPayload.verifyHashSize failed. hashSize={str(len(network_envelope.persistable_network_payload.get_hash()))}; object={to_truncated_string(proto)}")
                    if self.report_invalid_request(RuleViolation.MAX_MSG_SIZE_EXCEEDED):
                        return

                if exceeds:
                    logger.warning(f"size > MAX_MSG_SIZE. size={str(size)}; object={to_truncated_string(proto)}")
                    if self.report_invalid_request(RuleViolation.MAX_MSG_SIZE_EXCEEDED):
                        return
                    
                if self.violates_throttle_limit() and self.report_invalid_request(RuleViolation.THROTTLE_LIMIT_EXCEEDED):
                    return
                
                # Check P2P network ID
                if proto.message_version != Version.get_p2p_message_version() and self.report_invalid_request(RuleViolation.WRONG_NETWORK_ID):
                    logger.warning(f"RuleViolation.WRONG_NETWORK_ID. version of message={proto.message_version}, app version={Version.get_p2p_message_version()}, proto.toTruncatedString={to_truncated_string(proto)}")
                    return

                caused_shut_down = self.maybe_handle_supported_capabilities_message(network_envelope)
                if caused_shut_down:
                    return

                if isinstance(network_envelope, CloseConnectionMessage):
                    # If we get a CloseConnectionMessage we shut down
                    logger.debug(f"CloseConnectionMessage received. Reason={proto.close_connection_message.reason}\n\tconnection={self}")

                    if CloseConnectionReason.PEER_BANNED.name == proto.close_connection_message.reason:
                        logger.warning(f"We got shut down because we are banned by the other peer. Peer: {self.peers_node_address}")
                        self.shut_down(CloseConnectionReason.CLOSE_REQUESTED_BY_PEER)
                        return
                elif not self.stopped:
                    # We don't want to get the activity ts updated by ping/pong msg
                    if not isinstance(network_envelope, KeepAliveMessage):
                        self.statistic.update_last_activity_timestamp()
                    
                    # If SendersNodeAddressMessage we do some verifications and apply if successful,
                    # otherwise we return false.
                    if isinstance(network_envelope, SendersNodeAddressMessage):
                        is_valid = self.process_senders_node_address_message(network_envelope)
                        if not is_valid:
                            return

                    if not isinstance(network_envelope, SendersNodeAddressMessage) and not self.peers_node_address:
                        logger.info(f"We got a {network_envelope.__class__.__name__} from a peer with yet unknown address on connection with uid={self.uid}")

                    self.on_message(network_envelope, self)
                    UserThread.execute(lambda: self.connection_statistics.add_received_msg_metrics(get_time_ms() - ts, size))
        except (ProtobufferException, InvalidProtocolBufferException) as e:
            logger.error(e)
            self.report_invalid_request(RuleViolation.INVALID_DATA_TYPE)
        except Exception as e:
            self.handle_exception(e)

    def maybe_handle_supported_capabilities_message(self, network_envelope: 'NetworkEnvelope') -> bool:
        if not isinstance(network_envelope, SupportedCapabilitiesMessage):
            return False

        supported_capabilities = network_envelope.supported_capabilities
        if not supported_capabilities or supported_capabilities.is_empty():
            return False

        if self.capabilities == supported_capabilities:
            return False

        if not Capabilities.has_mandatory_capability(supported_capabilities):
            logger.info(f"We close a connection because of CloseConnectionReason.MANDATORY_CAPABILITIES_NOT_SUPPORTED "
                        f"to node {self.get_sender_node_address_as_string(network_envelope)}. Capabilities of old node: f{supported_capabilities.pretty_print()}, "
                        f"networkEnvelope class name={network_envelope.__class__.__name__}")
            self.shut_down(CloseConnectionReason.MANDATORY_CAPABILITIES_NOT_SUPPORTED)
            return True

        self.capabilities = supported_capabilities
        for listener in self.capabilities_listeners:
            if listener is not None:
                UserThread.execute(lambda: listener.on_changed(supported_capabilities))

        return False
    
    def get_sender_node_address(self, network_envelope: 'NetworkEnvelope'):
        if self.peers_node_address:
            return self.peers_node_address
        elif isinstance(network_envelope, SendersNodeAddressMessage):
            return network_envelope.sender_node_address
        else:
            return None

    def get_sender_node_address_as_string(self, network_envelope):
        node_address = self.get_sender_node_address(network_envelope)
        return "None" if node_address is None else node_address.get_full_address()