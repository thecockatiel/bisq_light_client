from dataclasses import dataclass
from bisq.core.network.p2p.direct_message import DirectMessage
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.trade.protocol.trade_message import TradeMessage
import proto.pb_pb2 as protobuf

@dataclass(frozen=True, kw_only=True)
class DelayedPayoutTxSignatureRequest(TradeMessage, DirectMessage):
    sender_node_address: NodeAddress
    delayed_payout_tx: bytes
    delayed_payout_tx_seller_signature: bytes

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        envelope = self.get_network_envelope_builder()
        envelope.delayed_payout_tx_signature_request.CopyFrom(
            protobuf.DelayedPayoutTxSignatureRequest(
                uid=self.uid,
                trade_id=self.trade_id,
                sender_node_address=self.sender_node_address.to_proto_message(),
                delayed_payout_tx=self.delayed_payout_tx,
                delayed_payout_tx_seller_signature=self.delayed_payout_tx_seller_signature,
            )
        )
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.DelayedPayoutTxSignatureRequest, message_version: int):
        return DelayedPayoutTxSignatureRequest(
            message_version=message_version,
            uid=proto.uid,
            trade_id=proto.trade_id,
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            delayed_payout_tx=proto.delayed_payout_tx,
            delayed_payout_tx_seller_signature=proto.delayed_payout_tx_seller_signature,
        )

    def __str__(self) -> str:
        return (f"DelayedPayoutTxSignatureRequest("
                f"\n    sender_node_address={self.sender_node_address},"
                f"\n    delayed_payout_tx={self.delayed_payout_tx.hex()},"
                f"\n    delayed_payout_tx_seller_signature={self.delayed_payout_tx_seller_signature.hex()}"
                f"\n) {super().__str__()}")