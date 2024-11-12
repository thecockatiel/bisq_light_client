from dataclasses import dataclass
from bisq.core.network.p2p.direct_message import DirectMessage
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.trade.protocol.trade_message import TradeMessage
import proto.pb_pb2 as protobuf

# It is the last message in the take offer phase. We use MailboxMessage instead of DirectMessage to add more tolerance
# in case of network issues and as the message does not trigger further protocol execution.
@dataclass(kw_only=True)
class DepositTxMessage(TradeMessage, DirectMessage):
    sender_node_address: NodeAddress
    deposit_tx_without_witnesses: bytes

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        envelope = self.get_network_envelope_builder()
        envelope.deposit_tx_message.CopyFrom(
            protobuf.DepositTxMessage(
                uid=self.uid,
                trade_id=self.trade_id,
                sender_node_address=self.sender_node_address.to_proto_message(),
                deposit_tx_without_witnesses=self.deposit_tx_without_witnesses,
            )
        )
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.DepositTxMessage, message_version: int):
        return DepositTxMessage(
            message_version=message_version,
            uid=proto.uid,
            trade_id=proto.trade_id,
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            deposit_tx_without_witnesses=proto.deposit_tx_without_witnesses,
        )

    def __str__(self) -> str:
        return (f"DepositTxMessage("
                f"\n    sender_node_address={self.sender_node_address},"
                f"\n    deposit_tx_without_witnesses={self.deposit_tx_without_witnesses.hex()}"
                f"\n) {super().__str__()}")