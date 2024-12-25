from dataclasses import dataclass
from bisq.core.network.p2p.storage.messages.broadcast_message import BroadcastMessage
import proto.pb_pb2 as protobuf


@dataclass(kw_only=True)
class RefreshOfferMessage(BroadcastMessage):
    hash_of_data_and_seq_nr: bytes  # 32 bytes
    signature: bytes  # 46 bytes
    hash_of_payload: bytes  # 32 bytes
    sequence_number: int  # 4 bytes

    def to_proto_network_envelope(self):
        envelope = self.get_network_envelope_builder()
        refresh_offer_message = protobuf.RefreshOfferMessage(
            hash_of_data_and_seq_nr=self.hash_of_data_and_seq_nr,
            signature=self.signature,
            hash_of_payload=self.hash_of_payload,
            sequence_number=self.sequence_number,
        )
        envelope.refresh_offer_message.CopyFrom(refresh_offer_message)
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.RefreshOfferMessage, message_version: int):
        return RefreshOfferMessage(
            message_version=message_version,
            hash_of_data_and_seq_nr=proto.hash_of_data_and_seq_nr,
            signature=proto.signature,
            hash_of_payload=proto.hash_of_payload,
            sequence_number=proto.sequence_number,
        )

    def __hash__(self):
        return hash(
            (
                self.hash_of_data_and_seq_nr,
                self.signature,
                self.hash_of_payload,
                self.sequence_number,
            )
        )
