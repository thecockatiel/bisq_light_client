 

from threading import RLock
import socket
from typing import TYPE_CHECKING
from bisq.core.network.p2p.peers.keepalive.messages.keep_alive_message import KeepAliveMessage
from proto.delimited_protobuf import write_delimited
from bisq.common.setup.log_setup import get_logger
from utils.concurrency import AtomicBoolean
from utils.time import get_time_ms

logger = get_logger(__name__)

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_envelope import NetworkEnvelope
    from bisq.core.network.p2p.network.statistic import Statistic
    from io import BufferedWriter

class ProtoOutputStream:
    def __init__(self, output_stream: 'socket.SocketIO', statistic: 'Statistic'):
        self.output_stream = output_stream
        self.statistic = statistic
        self.is_connection_active = AtomicBoolean(True)
        self.lock = RLock()

    def write_envelope(self, envelope: 'NetworkEnvelope'):
        with self.lock:
            try:
                self._write_envelope_or_throw(envelope)
            except (IOError, BrokenPipeError, ConnectionError) as e:
                if not self.is_connection_active.get():
                    # Connection was closed by us.
                    return
                # we don't want log to be flooded with failed to write envelope messages with stack traces if its simply any ConnectionError
                logger.error(f"Failed to write envelope, reason: {e}", exc_info=e if not isinstance(e, (ConnectionError, BrokenPipeError)) else None)
                raise

    def on_connection_shutdown(self):
        self.is_connection_active.set(False)

    def _write_envelope_or_throw(self, envelope: 'NetworkEnvelope'):
        ts = get_time_ms()
        proto = envelope.to_proto_network_envelope()
        write_delimited(self.output_stream, proto)
        self.output_stream.flush()
        duration = get_time_ms() - ts
        if duration > 10_000:
            logger.info(f"Sending {envelope.__class__.__name__} to peer took {duration / 1000.0} sec.")
        self.statistic.add_sent_bytes(proto.ByteSize())
        self.statistic.add_sent_message(envelope)
        if not isinstance(envelope, KeepAliveMessage):
            self.statistic.update_last_activity_timestamp()
