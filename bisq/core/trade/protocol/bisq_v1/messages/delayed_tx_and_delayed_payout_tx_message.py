from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.trade.protocol.bisq_v1.messages.trade_mailbox_message import TradeMailboxMessage 
import pb_pb2 as protobuf
from utils.data import raise_required

if TYPE_CHECKING:
    from bisq.core.protocol.core_proto_resolver import CoreProtoResolver

# It is the last message in the take offer phase. We use MailboxMessage instead of DirectMessage to add more tolerance
# in case of network issues and as the message does not trigger further protocol execution.
@dataclass
class DepositTxAndDelayedPayoutTxMessage(TradeMailboxMessage):
    sender_node_address: NodeAddress = field(default_factory=raise_required)
    deposit_tx: bytes = field(default_factory=raise_required)
    delayed_payout_tx: bytes = field(default_factory=raise_required)
    # Added at v1.7.0
    seller_payment_account_payload: Optional[PaymentAccountPayload] = field(default=None)

    def to_proto_network_envelope(self):
        message = protobuf.DepositTxAndDelayedPayoutTxMessage(
            uid=self.uid,
            trade_id=self.trade_id,
            sender_node_address=self.sender_node_address.to_proto_message(),
            deposit_tx=self.deposit_tx,
            delayed_payout_tx=self.delayed_payout_tx,
        )

        if self.seller_payment_account_payload:
            message.seller_payment_account_payload.CopyFrom(
                self.seller_payment_account_payload.to_proto_message()
            )

        envelope = self.get_network_envelope_builder()
        envelope.deposit_tx_and_delayed_payout_tx_message.CopyFrom(message)
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.DepositTxAndDelayedPayoutTxMessage, core_proto_resolver: "CoreProtoResolver", message_version: int):
        seller_payment_account_payload = (
            core_proto_resolver.from_proto(proto.seller_payment_account_payload)
            if proto.HasField('seller_payment_account_payload')
            else None
        )
        return DepositTxAndDelayedPayoutTxMessage(
            message_version=message_version,
            trade_id=proto.trade_id,
            uid=proto.uid,
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            deposit_tx=proto.deposit_tx,
            delayed_payout_tx=proto.delayed_payout_tx,
            seller_payment_account_payload=seller_payment_account_payload,
        )

    def __str__(self):
        return (f"DepositTxAndDelayedPayoutTxMessage("
                f"\n     sender_node_address={self.sender_node_address},"
                f"\n     deposit_tx={bytes_as_hex_string(self.deposit_tx)},"
                f"\n     delayed_payout_tx={bytes_as_hex_string(self.delayed_payout_tx)}"
                f"\n) {super().__str__()}")