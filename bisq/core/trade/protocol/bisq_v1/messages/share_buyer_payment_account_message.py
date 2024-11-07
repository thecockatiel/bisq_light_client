from dataclasses import dataclass

from bisq.core.network.p2p.network.core_proto_resolver import CoreProtoResolver
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.trade.protocol.bisq_v1.messages.trade_mailbox_message import (
    TradeMailboxMessage,
)
import proto.pb_pb2 as protobuf


# Added at v1.7.0
@dataclass(frozen=True, kw_only=True)
class ShareBuyerPaymentAccountMessage(TradeMailboxMessage):
    sender_node_address: NodeAddress
    buyer_payment_account_payload: PaymentAccountPayload

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        envelope = self.get_network_envelope_builder()
        envelope.share_buyer_payment_account_message.CopyFrom(
            protobuf.ShareBuyerPaymentAccountMessage(
                uid=self.uid,
                trade_id=self.trade_id,
                sender_node_address=self.sender_node_address.to_proto_message(),
                buyer_payment_account_payload=self.buyer_payment_account_payload.to_proto_message(),
            )
        )
        return envelope

    @staticmethod
    def from_proto(
        proto: protobuf.ShareBuyerPaymentAccountMessage,
        core_proto_resolver: CoreProtoResolver,
        message_version: int,
    ) -> "ShareBuyerPaymentAccountMessage":
        buyer_payment_account_payload = (
            core_proto_resolver.from_proto(proto.buyer_payment_account_payload)
            if proto.buyer_payment_account_payload
            else None
        )
        return ShareBuyerPaymentAccountMessage(
            message_version=message_version,
            uid=proto.uid,
            trade_id=proto.trade_id,
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            buyer_payment_account_payload=buyer_payment_account_payload,
        )

    def __str__(self) -> str:
        return f"ShareBuyerPaymentAccountMessage({{\n    sender_node_address={self.sender_node_address}\n}} {super().__str__()})"
