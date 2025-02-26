from typing import TYPE_CHECKING
from bisq.common.crypto.pub_key_ring import PubKeyRing
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.trade.protocol.bsq_swap.messages.bsq_swap_request import BsqSwapRequest
from bisq.core.trade.protocol.bsq_swap.messages.tx_inputs_message import TxInputsMessage
import pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.btc.raw_transaction_input import RawTransactionInput


class BuyersBsqSwapRequest(BsqSwapRequest, TxInputsMessage):

    def __init__(
        self,
        trade_id: str,
        sender_node_address: "NodeAddress",
        taker_pub_key_ring: "PubKeyRing",
        trade_amount: int,
        tx_fee_per_vbyte: int,
        maker_fee: int,
        taker_fee: int,
        trade_date: int,
        bsq_inputs: list["RawTransactionInput"],
        bsq_change: int,
        buyers_btc_payout_address: str,
        buyers_bsq_change_address: str,
        uid: str = None,
        message_version: int = None,
    ):
        super().__init__(
            trade_id=trade_id,
            sender_node_address=sender_node_address,
            taker_pub_key_ring=taker_pub_key_ring,
            trade_amount=trade_amount,
            tx_fee_per_vbyte=tx_fee_per_vbyte,
            maker_fee=maker_fee,
            taker_fee=taker_fee,
            trade_date=trade_date,
            uid=uid,
            message_version=message_version,
        )
        self.bsq_inputs = bsq_inputs
        self.bsq_change = bsq_change
        self.buyers_btc_payout_address = buyers_btc_payout_address
        self.buyers_bsq_change_address = buyers_bsq_change_address

    def to_proto_message(self):
        return protobuf.BuyersBsqSwapRequest(
            uid=self.uid,
            trade_id=self.trade_id,
            sender_node_address=self.sender_node_address.to_proto_message(),
            taker_pub_key_ring=self.taker_pub_key_ring.to_proto_message(),
            trade_amount=self.trade_amount,
            tx_fee_per_vbyte=self.tx_fee_per_vbyte,
            maker_fee=self.maker_fee,
            taker_fee=self.taker_fee,
            trade_date=self.trade_date,
            bsq_inputs=[input.to_proto_message() for input in self.bsq_inputs],
            bsq_change=self.bsq_change,
            buyers_btc_payout_address=self.buyers_btc_payout_address,
            buyers_bsq_change_address=self.buyers_bsq_change_address,
        )

    def to_proto_network_envelope(self):
        builder = self.get_network_envelope_builder()
        builder.buyers_bsq_swap_request.CopyFrom(self.to_proto_message())
        return builder

    @staticmethod
    def from_proto(proto: protobuf.BuyersBsqSwapRequest, message_version: int):
        return BuyersBsqSwapRequest(
            message_version=message_version,
            trade_id=proto.trade_id,
            uid=proto.uid,
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            taker_pub_key_ring=PubKeyRing.from_proto(proto.taker_pub_key_ring),
            trade_amount=proto.trade_amount,
            tx_fee_per_vbyte=proto.tx_fee_per_vbyte,
            maker_fee=proto.maker_fee,
            taker_fee=proto.taker_fee,
            trade_date=proto.trade_date,
            bsq_inputs=[
                RawTransactionInput.from_proto(input) for input in proto.bsq_inputs
            ],
            bsq_change=proto.bsq_change,
            buyers_btc_payout_address=proto.buyers_btc_payout_address,
            buyers_bsq_change_address=proto.buyers_bsq_change_address,
        )
