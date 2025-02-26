from bisq.common.crypto.pub_key_ring import PubKeyRing
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.trade.protocol.bsq_swap.messages.bsq_swap_request import BsqSwapRequest
import pb_pb2 as protobuf


class SellersBsqSwapRequest(BsqSwapRequest):

    def to_proto_message(self):
        return protobuf.SellersBsqSwapRequest(
            uid=self.uid,
            trade_id=self.trade_id,
            sender_node_address=self.sender_node_address.to_proto_message(),
            taker_pub_key_ring=self.taker_pub_key_ring.to_proto_message(),
            trade_amount=self.trade_amount,
            tx_fee_per_vbyte=self.tx_fee_per_vbyte,
            maker_fee=self.maker_fee,
            taker_fee=self.taker_fee,
            trade_date=self.trade_date,
        )

    def to_proto_network_envelope(self):
        builder = self.get_network_envelope_builder()
        builder.sellers_bsq_swap_request.CopyFrom(self.to_proto_message())
        return builder

    @staticmethod
    def from_proto(proto: protobuf.SellersBsqSwapRequest, message_version: int):
        return SellersBsqSwapRequest(
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
        )
