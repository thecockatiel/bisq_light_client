from dataclasses import dataclass
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.trade.protocol.bisq_v1.messages.trade_mailbox_message import TradeMailboxMessage
import proto.pb_pb2 as protobuf

@dataclass(frozen=True, kw_only=True)
class MediatedPayoutTxPublishedMessage(TradeMailboxMessage):
    payout_tx: bytes
    sender_node_address: NodeAddress 

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        envelope = self.get_network_envelope_builder()
        envelope.mediated_payout_tx_published_message.CopyFrom(
            protobuf.MediatedPayoutTxPublishedMessage(
                trade_id=self.trade_id,
                payout_tx=self.payout_tx,
                sender_node_address=self.sender_node_address.to_proto_message(),
                uid=self.uid,
            )
        )
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.MediatedPayoutTxPublishedMessage, 
                  message_version: int) -> 'MediatedPayoutTxPublishedMessage':
        return MediatedPayoutTxPublishedMessage(
            message_version=message_version,
            trade_id=proto.trade_id,
            uid=proto.uid,
            payout_tx=proto.payout_tx,
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
        )

    def __str__(self) -> str:
        return (f"MediatedPayoutTxPublishedMessage("
                f"\n     payout_tx={self.payout_tx.hex()}"
                f",\n     sender_node_address={self.sender_node_address}"
                f",\n     uid='{self.uid}'"
                f"\n) {super().__str__()}")