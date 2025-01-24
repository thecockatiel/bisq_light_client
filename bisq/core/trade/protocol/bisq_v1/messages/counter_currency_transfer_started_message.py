from dataclasses import dataclass, field
from typing import Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.trade.protocol.bisq_v1.messages.trade_mailbox_message import TradeMailboxMessage
import pb_pb2 as protobuf
from utils.data import raise_required


@dataclass
class CounterCurrencyTransferStartedMessage(TradeMailboxMessage):
    buyer_payout_address: str = field(default_factory=raise_required)
    sender_node_address: NodeAddress = field(default_factory=raise_required)
    buyer_signature: bytes = field(default_factory=raise_required)
    counter_currency_tx_id: Optional[str] = field(default=None)
    counter_currency_extra_data: Optional[str] = field(default=None)

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        builder = protobuf.CounterCurrencyTransferStartedMessage(
            trade_id=self.trade_id,
            buyer_payout_address=self.buyer_payout_address,
            sender_node_address=self.sender_node_address.to_proto_message(),
            buyer_signature=protobuf(value=self.buyer_signature),
            uid=self.uid,
        )

        if self.counter_currency_tx_id:
            builder.counter_currency_tx_id = self.counter_currency_tx_id
        if self.counter_currency_extra_data:
            builder.counter_currency_extra_data = self.counter_currency_extra_data

        envelope = self.get_network_envelope_builder()
        envelope.counter_currency_transfer_started_message.CopyFrom(builder)
        return envelope

    @staticmethod
    def from_proto(
        proto: protobuf.CounterCurrencyTransferStartedMessage, message_version: int
    ) -> "CounterCurrencyTransferStartedMessage":
        return CounterCurrencyTransferStartedMessage(
            message_version=message_version,
            trade_id=proto.trade_id,
            uid=proto.uid,
            buyer_payout_address=proto.buyer_payout_address,
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            buyer_signature=proto.buyer_signature,
            counter_currency_tx_id=ProtoUtil.string_or_none_from_proto(
                proto.counter_currency_tx_id
            ),
            counter_currency_extra_data=ProtoUtil.string_or_none_from_proto(
                proto.counter_currency_extra_data
            ),
        )

    def __str__(self) -> str:
        return (
            f"CounterCurrencyTransferStartedMessage({{\n"
            f"    buyer_payout_address: '{self.buyer_payout_address}',\n"
            f"    sender_node_address: {self.sender_node_address},\n"
            f"    counter_currency_tx_id: {self.counter_currency_tx_id},\n"
            f"    counter_currency_extra_data: {self.counter_currency_extra_data},\n"
            f"    uid: '{self.uid}',\n"
            f"    buyer_signature: {self.buyer_signature.hex()}\n"
            f"}} {super().__str__()}"
        )
