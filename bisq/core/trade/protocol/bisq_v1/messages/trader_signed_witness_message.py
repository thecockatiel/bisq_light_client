from dataclasses import dataclass

from bisq.core.account.sign.signed_witness import SignedWitness
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.trade.protocol.bisq_v1.messages.trade_mailbox_message import (
    TradeMailboxMessage,
)
import proto.pb_pb2 as protobuf


# "Not used anymore since v1.4.0"
@dataclass(kw_only=True)
class TraderSignedWitnessMessage(TradeMailboxMessage):
    sender_node_address: NodeAddress
    signed_witness: SignedWitness

    def to_proto_network_envelope(self) -> "protobuf.NetworkEnvelope":
        message = protobuf.TraderSignedWitnessMessage(
            uid=self.uid,
            trade_id=self.trade_id,
            sender_node_address=self.sender_node_address.to_proto_message(),
            signed_witness=self.signed_witness.to_proto_signed_witness(),
        )
        
        envelope = self.get_network_envelope_builder()
        envelope.trader_signed_witness_message.CopyFrom(message)

        return envelope

    @staticmethod
    def from_proto(proto: protobuf.TraderSignedWitnessMessage, message_version: int
    ) -> "TraderSignedWitnessMessage":
        return TraderSignedWitnessMessage(
            message_version=message_version,
            uid=proto.uid,
            trade_id=proto.trade_id,
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            signed_witness=SignedWitness.from_proto(proto.signed_witness),
        )

    def __str__(self) -> str:
        return (
            f"TraderSignedWitnessMessage("
            f"\n     sender_node_address={self.sender_node_address}"
            f"\n     signed_witness={self.signed_witness}"
            f"\n) {super().__str__()}"
        )
