from dataclasses import dataclass
import bisq.core.common.version as Version
from bisq.core.network.p2p.storage.messages.broadcast_message import BroadcastMessage
import proto.pb_pb2 as protobuf

@dataclass(frozen=True)
class RefreshOfferMessage(BroadcastMessage):
    hash_of_data_and_seq_nr: bytes    # 32 bytes
    signature: bytes                  # 46 bytes
    hash_of_payload: bytes            # 32 bytes
    sequence_number: int              # 4 bytes

    def __init__(self, hash_of_data_and_seq_nr: bytes, signature: bytes, hash_of_payload: bytes, sequence_number: int, message_version=Version.get_p2p_message_version()):
        super().__init__(message_version)
        self.hash_of_data_and_seq_nr = hash_of_data_and_seq_nr
        self.signature = signature
        self.hash_of_payload = hash_of_payload
        self.sequence_number = sequence_number

    def to_proto_network_envelope(self):
        envelope = self.get_network_envelope_builder()
        refresh_offer_message = protobuf.RefreshOfferMessage(
            hash_of_data_and_seq_nr=self.hash_of_data_and_seq_nr,
            signature=self.signature,
            hash_of_payload=self.hash_of_payload,
            sequence_number=self.sequence_number
        )
        envelope.refresh_offer_message.CopyFrom(refresh_offer_message)
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.RefreshOfferMessage, message_version: int):
        return RefreshOfferMessage(
            proto.hash_of_data_and_seq_nr,
            proto.signature,
            proto.hash_of_payload,
            proto.sequence_number,
            message_version
        )