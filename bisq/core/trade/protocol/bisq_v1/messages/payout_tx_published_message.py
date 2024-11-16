from dataclasses import dataclass
from typing import Optional
import uuid

from bisq.core.account.sign.signed_witness import SignedWitness
import bisq.common.version as Version
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.trade.protocol.bisq_v1.messages.trade_mailbox_message import (
    TradeMailboxMessage,
)
import proto.pb_pb2 as protobuf


class PayoutTxPublishedMessage(TradeMailboxMessage):
    payout_tx: bytes
    sender_node_address: NodeAddress
    signed_witness: Optional[SignedWitness] = None

    def __init__(
        self,
        trade_id: str,
        payout_tx: bytes,
        sender_node_address: NodeAddress,
        signed_witness: Optional[SignedWitness] = None,
        uid: str = str(uuid.uuid4()),
        message_version: int = Version.get_p2p_message_version(),
    ):
        super().__init__(message_version=message_version, uid=uid, trade_id=trade_id)
        self.payout_tx = payout_tx
        self.sender_node_address = sender_node_address
        self.signed_witness = signed_witness

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        envelope = self.get_network_envelope_builder()
        msg = protobuf.PayoutTxPublishedMessage(
            trade_id=self.trade_id,
            payout_tx=self.payout_tx,
            sender_node_address=self.sender_node_address.to_proto_message(),
            uid=self.uid,
        )
        if self.signed_witness:
            msg.signed_witness.CopyFrom(self.signed_witness.to_proto_signed_witness())
        envelope.payout_tx_published_message.CopyFrom(msg)
        return envelope

    @staticmethod
    def from_proto(
        proto: protobuf.PayoutTxPublishedMessage, message_version: int
    ) -> "PayoutTxPublishedMessage":
        # There is no method to check for a nullable non-primitive data type object but we know that all fields
        # are empty/null, so we check for the signature to see if we got a valid signedWitness.
        signed_witness = None
        if proto.signed_witness and proto.signed_witness.signature:
            signed_witness = SignedWitness.from_proto(proto.signed_witness)

        return PayoutTxPublishedMessage(
            trade_id=proto.trade_id,
            payout_tx=bytes(proto.payout_tx),
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            signed_witness=signed_witness,
            uid=proto.uid,
            message_version=message_version,
        )

    def __str__(self) -> str:
        return (
            f"PayoutTxPublishedMessage("
            f"payoutTx={self.payout_tx.hex()}, "
            f"senderNodeAddress={self.sender_node_address}, "
            f"signedWitness={self.signed_witness}"
            f") {super().__str__()}"
        )
