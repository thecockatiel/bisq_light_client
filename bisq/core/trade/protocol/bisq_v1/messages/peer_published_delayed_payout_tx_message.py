from dataclasses import dataclass, field
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.trade.protocol.bisq_v1.messages.trade_mailbox_message import (
    TradeMailboxMessage,
)
import pb_pb2 as protobuf
from utils.data import raise_required


@dataclass
class PeerPublishedDelayedPayoutTxMessage(TradeMailboxMessage):
    sender_node_address: NodeAddress = field(default_factory=raise_required)

    def to_proto_network_envelope(self) -> "protobuf.NetworkEnvelope":
        envelope = self.get_network_envelope_builder()
        envelope.peer_published_delayed_payout_tx_message.CopyFrom(
            protobuf.PeerPublishedDelayedPayoutTxMessage(
                uid=self.uid,
                trade_id=self.trade_id,
                sender_node_address=self.sender_node_address.to_proto_message(),
            )
        )
        return envelope

    @staticmethod
    def from_proto(
        proto: protobuf.PeerPublishedDelayedPayoutTxMessage, message_version: int
    ) -> "PeerPublishedDelayedPayoutTxMessage":
        return PeerPublishedDelayedPayoutTxMessage(
            message_version=message_version,
            uid=proto.uid,
            trade_id=proto.trade_id,
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
        )

    def __str__(self) -> str:
        return (
            f"PeerPublishedDelayedPayoutTxMessage("
            f"\n     sender_node_address={self.sender_node_address}"
            f"\n) {super().__str__()}"
        )
