from abc import ABC 
from google.protobuf.message import Message
from bisq.core.common.envelope import Envelope
import proto.pb_pb2 as protobuf
# Import protobuf modules as needed

class NetworkEnvelope(Envelope, ABC):
    message_version: int

    # PROTO BUFFER

    def __init__(self, message_version: int):
        self.message_version = message_version

    def get_network_envelope_builder(self):
        return protobuf.NetworkEnvelope(message_version=self.message_version)

    def to_proto_message(self) -> Message:
        return self.get_network_envelope_builder()

    def to_proto_network_envelope(self):
        return self.get_network_envelope_builder()

    # API

    def get_message_version(self) -> int:
        # -1 is used for the case that we use an envelope message as payload (mailbox)
        # so we check only against 0 which is the default value if not set
        if self.message_version == 0:
            raise ValueError("messageVersion is not set (0).")
        return self.message_version

    def __str__(self):
        return f"NetworkEnvelope{{\n     messageVersion={self.message_version}\n}}"