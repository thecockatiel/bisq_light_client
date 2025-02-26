from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.trade.protocol.bsq_swap.messages.tx_inputs_message import TxInputsMessage
from bisq.core.trade.protocol.trade_message import TradeMessage
import pb_pb2 as protobuf
from bisq.core.btc.raw_transaction_input import RawTransactionInput


class BsqSwapTxInputsMessage(TradeMessage, TxInputsMessage):
    def __init__(
        self,
        trade_id: str,
        sender_node_address: "NodeAddress",
        bsq_inputs: tuple["RawTransactionInput"],
        bsq_change: int,
        buyers_btc_payout_address: str,
        buyers_bsq_change_address: str,
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
        self.bsq_inputs = bsq_inputs
        self.bsq_change = bsq_change
        self.buyers_btc_payout_address = buyers_btc_payout_address
        self.buyers_bsq_change_address = buyers_bsq_change_address

    def to_proto_message(self):
        return protobuf.BsqSwapTxInputsMessage(
            uid=self.uid,
            trade_id=self.trade_id,
            sender_node_address=self.sender_node_address.to_proto_message(),
            bsq_inputs=[input.to_proto_message() for input in self.bsq_inputs],
            bsq_change=self.bsq_change,
            buyers_btc_payout_address=self.buyers_btc_payout_address,
            buyers_bsq_change_address=self.buyers_bsq_change_address,
        )

    def to_proto_network_envelope(self):
        builder = self.get_network_envelope_builder()
        builder.bsq_swap_tx_inputs_message.CopyFrom(self.to_proto_message())
        return builder

    @staticmethod
    def from_proto(proto: protobuf.BsqSwapTxInputsMessage, message_version: int):
        return BsqSwapTxInputsMessage(
            message_version=message_version,
            trade_id=proto.trade_id,
            uid=proto.uid,
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            bsq_inputs=tuple(
                RawTransactionInput.from_proto(input) for input in proto.bsq_inputs
            ),
            bsq_change=proto.bsq_change,
            buyers_btc_payout_address=proto.buyers_btc_payout_address,
            buyers_bsq_change_address=proto.buyers_bsq_change_address,
        )

    def __eq__(self, other):
        return (
            isinstance(other, BsqSwapTxInputsMessage)
            and super().__eq__(other)
            and self.sender_node_address == other.sender_node_address
            and self.bsq_inputs == other.bsq_inputs
            and self.bsq_change == other.bsq_change
            and self.buyers_btc_payout_address == other.buyers_btc_payout_address
            and self.buyers_bsq_change_address == other.buyers_bsq_change_address
        )

    def __hash__(self):
        return hash(
            (
                super().__hash__(),
                self.sender_node_address,
                self.bsq_inputs,
                self.bsq_change,
                self.buyers_btc_payout_address,
                self.buyers_bsq_change_address,
            )
        )
