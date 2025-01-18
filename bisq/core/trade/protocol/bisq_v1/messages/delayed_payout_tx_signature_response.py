from dataclasses import dataclass, field 
from bisq.core.network.p2p.direct_message import DirectMessage
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.trade.protocol.trade_message import TradeMessage
import proto.pb_pb2 as protobuf
from utils.data import raise_required

@dataclass
class DelayedPayoutTxSignatureResponse(TradeMessage, DirectMessage):
    sender_node_address: NodeAddress = field(default_factory=raise_required)
    delayed_payout_tx_buyer_signature: bytes = field(default_factory=raise_required)
    deposit_tx: bytes = field(default_factory=raise_required)

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        envelope = self.get_network_envelope_builder()
        envelope.delayed_payout_tx_signature_response.CopyFrom(
            protobuf.DelayedPayoutTxSignatureResponse(
                uid=self.uid,
                trade_id=self.trade_id,
                sender_node_address=self.sender_node_address.to_proto_message(),
                delayed_payout_tx_buyer_signature=self.delayed_payout_tx_buyer_signature,
                deposit_tx=self.deposit_tx,
            )
        )
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.DelayedPayoutTxSignatureResponse, message_version: int):
        return DelayedPayoutTxSignatureResponse(
            message_version=message_version,
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            delayed_payout_tx_buyer_signature=proto.delayed_payout_tx_buyer_signature,
            deposit_tx=proto.deposit_tx,
            trade_id=proto.trade_id,
            uid=proto.uid,
        )

    def __str__(self) -> str:
        return (f"DelayedPayoutTxSignatureResponse("
                f"\n    sender_node_address={self.sender_node_address},"
                f"\n    delayed_payout_tx_buyer_signature={self.delayed_payout_tx_buyer_signature.hex()},"
                f"\n    deposit_tx={self.deposit_tx.hex()}"
                f"\n) {super().__str__()}")