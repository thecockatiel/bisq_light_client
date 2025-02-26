from bisq.core.network.p2p.direct_message import DirectMessage
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.trade.protocol.trade_message import TradeMessage
import pb_pb2 as protobuf
from bisq.core.btc.raw_transaction_input import RawTransactionInput


class BsqSwapFinalizeTxRequest(TradeMessage, DirectMessage):
    def __init__(
        self,
        trade_id: str,
        sender_node_address: "NodeAddress",
        tx: bytes,
        btc_inputs: list["RawTransactionInput"],
        btc_change: int,
        bsq_payout_address: str,
        btc_change_address: str,
        uid: str = None,
        message_version: int = None,
    ):
        super_kwargs = {
            "message_version": message_version,
            "trade_id": trade_id,
            "uid": uid,
        }
        # filter out the none values from the super to allow default values to be used
        super_kwargs = {k: v for k, v in super_kwargs.items() if v is not None}
        super().__init__(**super_kwargs)
        self.sender_node_address = sender_node_address
        self.tx = tx
        self.btc_inputs = btc_inputs
        self.btc_change = btc_change
        self.bsq_payout_address = bsq_payout_address
        self.btc_change_address = btc_change_address

    def to_proto_message(self):
        return protobuf.BsqSwapFinalizeTxRequest(
            uid=self.uid,
            trade_id=self.trade_id,
            sender_node_address=self.sender_node_address.to_proto_message(),
            tx=self.tx,
            btc_inputs=[input.to_proto_message() for input in self.btc_inputs],
            btc_change=self.btc_change,
            bsq_payout_address=self.bsq_payout_address,
            btc_change_address=self.btc_change_address,
        )

    def to_proto_network_envelope(self):
        builder = self.get_network_envelope_builder()
        builder.bsq_swap_finalize_tx_request.CopyFrom(self.to_proto_message())
        return builder

    @staticmethod
    def from_proto(proto: protobuf.BsqSwapFinalizeTxRequest, message_version: int):
        return BsqSwapFinalizeTxRequest(
            message_version=message_version,
            trade_id=proto.trade_id,
            uid=proto.uid,
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            tx=proto.tx,
            btc_inputs=[
                RawTransactionInput.from_proto(input) for input in proto.btc_inputs
            ],
            btc_change=proto.btc_change,
            bsq_payout_address=proto.bsq_payout_address,
            btc_change_address=proto.btc_change,
        )

    def __str__(self):
        return (
            f"BsqSwapFinalizeTxRequest{{\n"
            f"    sender_node_address={self.sender_node_address},\n"
            f"    btc_inputs={self.btc_inputs},\n"
            f"    btc_change={self.btc_change},\n"
            f"    bsq_payout_address='{self.bsq_payout_address}',\n"
            f"    btc_change_address='{self.btc_change_address}'\n"
            f"}} {super().__str__()}"
        )
