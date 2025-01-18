 

from asyncio import StreamWriter
from typing import TYPE_CHECKING
from bisq.core.network.p2p.peers.keepalive.messages.keep_alive_message import KeepAliveMessage
from proto.delimited_protobuf import write_delimited
from bisq.core.network.p2p.network.bisq_runtime_exception import BisqRuntimeException
from bisq.common.setup.log_setup import get_logger
from utils.time import get_time_ms

logger = get_logger(__name__)

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_envelope import NetworkEnvelope
    from bisq.core.network.p2p.network.statistic import Statistic
    from io import BufferedWriter

class ProtoOutputStream:
    def __init__(self, output_stream: 'StreamWriter', statistic: 'Statistic'):
        self.output_stream = output_stream
        self.statistic = statistic
        self.is_connection_active = True

    async def write_envelope_async(self, envelope: 'NetworkEnvelope'):
        try:
            await self._write_envelope_or_throw(envelope)
        except IOError as e:
            if not self.is_connection_active:
                # Connection was closed by us.
                return
            logger.error("Failed to write envelope", exc_info=e)
            raise BisqRuntimeException("Failed to write envelope", e)

    def on_connection_shutdown(self):
        self.is_connection_active = False
        try:
            self.output_stream.close()
        except Exception as t:
            logger.error("Failed to close connection", exc_info=t)

    async def _write_envelope_or_throw(self, envelope: 'NetworkEnvelope'):
        ts = get_time_ms()
        proto = envelope.to_proto_network_envelope()
        write_delimited(self.output_stream, proto)
        await self.output_stream.drain()
        duration = get_time_ms() - ts
        if duration > 10_000:
            logger.info(f"Sending {envelope.__class__.__name__} to peer took {duration / 1000.0} sec.")
        self.statistic.add_sent_bytes(proto.ByteSize())
        self.statistic.add_sent_message(envelope)
        if not isinstance(envelope, KeepAliveMessage):
            self.statistic.update_last_activity_timestamp()

        