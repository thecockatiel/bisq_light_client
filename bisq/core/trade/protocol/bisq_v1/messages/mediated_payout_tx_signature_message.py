from dataclasses import dataclass, field

from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.trade.protocol.bisq_v1.messages.trade_mailbox_message import TradeMailboxMessage
import pb_pb2 as protobuf
from utils.data import raise_required
 
@dataclass
class MediatedPayoutTxSignatureMessage(TradeMailboxMessage):
    tx_signature: bytes = field(default_factory=raise_required)
    sender_node_address: NodeAddress = field(default_factory=raise_required)

    def to_proto_network_envelope(self):
        envelope = self.get_network_envelope_builder()
        envelope.mediated_payout_tx_signature_message.CopyFrom(
            protobuf.MediatedPayoutTxSignatureMessage(
                uid=self.uid,
                trade_id=self.trade_id,
                tx_signature=self.tx_signature,
                sender_node_address=self.sender_node_address.to_proto_message(),
            )
        )
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.MediatedPayoutTxSignatureMessage, message_version: int):
        return MediatedPayoutTxSignatureMessage(
            message_version=message_version,
            trade_id=proto.trade_id,
            uid=proto.uid,
            tx_signature=proto.tx_signature,
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
        )

    def get_trade_id(self) -> str:
        return self.trade_id

    def __str__(self) -> str:
        return (f"MediatedPayoutSignatureMessage("
                f"\n     tx_signature={self.tx_signature.hex()}"
                f",\n     trade_id='{self.trade_id}'"
                f",\n     sender_node_address={self.sender_node_address}"
                f"\n) {super().__str__()}")