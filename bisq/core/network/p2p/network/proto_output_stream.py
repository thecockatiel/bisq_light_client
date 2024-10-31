 

from threading import RLock
import time
from typing import TYPE_CHECKING

from bisq.core.network.p2p.peers.keepalive.keep_alive_message import KeepAliveMessage
from proto.delimited_protobuf import write_delimited

from .connection import Connection
from bisq.core.network.p2p.network.bisq_runtime_exception import BisqRuntimeException
from bisq.logging import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope
    from bisq.core.network.p2p.network.statistic import Statistic
    from google.protobuf.message import Message
    from io import BufferedWriter
    from socket import socket as Socket

class ProtoOutputStream:
    def __init__(self, socket: 'Socket', output_stream: 'BufferedWriter', statistic: 'Statistic'):
        self.socket = socket
        self.output_stream = output_stream
        self.statistic = statistic
        self.is_connection_active = True
        self.lock = RLock()

    def write_envelope(self, envelope: 'NetworkEnvelope'):
        with self.lock:
            try:
                self.write_envelope_or_throw(envelope)
            except IOError as e:
                if not self.is_connection_active:
                    # Connection was closed by us.
                    return
                logger.error("Failed to write envelope", e)
                raise BisqRuntimeException("Failed to write envelope", e)

    def on_connection_shutdown(self):
        self.is_connection_active = False
        acquired_lock = self.try_to_acquire_lock()
        if not acquired_lock:
            return
        try:
            self.output_stream.close()
        except Exception as t:
            logger.error("Failed to close connection", t)
        finally:
            self.lock.release()

    def write_envelope_or_throw(self, envelope: 'NetworkEnvelope'):
        ts = time.time_ns()
        proto = envelope.to_proto_network_envelope()
        write_delimited(self.output_stream, proto)
        self.output_stream.flush()
        duration = (time.time_ns() - ts) // 1_000_000
        if duration > 10_000:
            logger.info(f"Sending {envelope.__class__.__name__} to peer took {duration / 1000.0} sec.")
        self.statistic.add_sent_bytes(proto.get_serialized_size())
        self.statistic.add_sent_message(envelope)
        if not isinstance(envelope, KeepAliveMessage):
            self.statistic.update_last_activity_timestamp()

    def try_to_acquire_lock(self) -> bool: 
        return self.lock.acquire(False, Connection.SHUTDOWN_TIMEOUT / 1000)
        