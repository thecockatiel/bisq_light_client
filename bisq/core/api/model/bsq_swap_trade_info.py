from typing import TYPE_CHECKING, Optional
from bisq.common.payload import Payload
import grpc_pb2

if TYPE_CHECKING:
    from bisq.core.trade.model.bsq_swap.bsq_swap_trade import BsqSwapTrade


class BsqSwapTradeInfo(Payload):
    def __init__(
        self,
        tx_id: Optional[str] = None,
        bsq_trade_amount: int = 0,
        btc_trade_amount: int = 0,
        bsq_maker_trade_fee: int = 0,
        bsq_taker_trade_fee: int = 0,
        tx_fee_per_vbyte: int = 0,
        maker_bsq_address: Optional[str] = None,
        maker_btc_address: Optional[str] = None,
        taker_bsq_address: Optional[str] = None,
        taker_btc_address: Optional[str] = None,
        num_confirmations: int = 0,
        error_message: Optional[str] = None,
        payout: int = 0,
        swap_peer_payout: int = 0,
    ):
        self.tx_id = tx_id
        self.bsq_trade_amount = bsq_trade_amount
        self.btc_trade_amount = btc_trade_amount
        self.bsq_maker_trade_fee = bsq_maker_trade_fee
        self.bsq_taker_trade_fee = bsq_taker_trade_fee
        self.tx_fee_per_vbyte = tx_fee_per_vbyte
        self.maker_bsq_address = maker_bsq_address
        self.maker_btc_address = maker_btc_address
        self.taker_bsq_address = taker_bsq_address
        self.taker_btc_address = taker_btc_address
        self.num_confirmations = num_confirmations
        self.error_message = error_message
        self.payout = payout
        self.swap_peer_payout = swap_peer_payout

    @staticmethod
    def from_bsq_swap_trade(
        trade: "BsqSwapTrade", was_my_offer: bool, num_confirmations: int
    ) -> "BsqSwapTradeInfo":
        protocol_model = trade.bsq_swap_protocol_model
        swap_peer = protocol_model.trade_peer
        maker_bsq_address = (
            protocol_model.bsq_address if was_my_offer else swap_peer.bsq_address
        )
        maker_btc_address = (
            protocol_model.btc_address if was_my_offer else swap_peer.btc_address
        )
        taker_bsq_address = (
            swap_peer.bsq_address if was_my_offer else protocol_model.bsq_address
        )
        taker_btc_address = (
            swap_peer.btc_address if was_my_offer else protocol_model.btc_address
        )

        return BsqSwapTradeInfo(
            tx_id=trade.tx_id,
            bsq_trade_amount=trade.get_bsq_trade_amount(),
            btc_trade_amount=trade.get_amount_as_long(),
            bsq_maker_trade_fee=trade.maker_fee_as_long,
            bsq_taker_trade_fee=trade.taker_fee_as_long,
            tx_fee_per_vbyte=trade.tx_fee_per_vbyte(),
            maker_bsq_address=maker_bsq_address,
            maker_btc_address=maker_btc_address,
            taker_bsq_address=taker_bsq_address,
            taker_btc_address=taker_btc_address,
            num_confirmations=num_confirmations,
            error_message=trade.error_message,
            payout=protocol_model.payout,
            swap_peer_payout=swap_peer.payout,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self) -> grpc_pb2.BsqSwapTradeInfo:
        return grpc_pb2.BsqSwapTradeInfo(
            tx_id=self.tx_id if self.tx_id is not None else "",
            bsq_trade_amount=self.bsq_trade_amount,
            btc_trade_amount=self.btc_trade_amount,
            bsq_maker_trade_fee=self.bsq_maker_trade_fee,
            bsq_taker_trade_fee=self.bsq_taker_trade_fee,
            tx_fee_per_vbyte=self.tx_fee_per_vbyte,
            maker_bsq_address=(
                self.maker_bsq_address if self.maker_bsq_address is not None else ""
            ),
            taker_bsq_address=(
                self.taker_bsq_address if self.taker_bsq_address is not None else ""
            ),
            maker_btc_address=(
                self.maker_btc_address if self.maker_btc_address is not None else ""
            ),
            taker_btc_address=(
                self.taker_btc_address if self.taker_btc_address is not None else ""
            ),
            num_confirmations=self.num_confirmations,
            error_message=self.error_message if self.error_message is not None else "",
            payout=self.payout,
            swap_peer_payout=self.swap_peer_payout,
        )

    @staticmethod
    def from_proto(proto: grpc_pb2.BsqSwapTradeInfo) -> "BsqSwapTradeInfo":
        return BsqSwapTradeInfo(
            tx_id=proto.tx_id,
            bsq_trade_amount=proto.bsq_trade_amount,
            btc_trade_amount=proto.btc_trade_amount,
            bsq_maker_trade_fee=proto.bsq_maker_trade_fee,
            bsq_taker_trade_fee=proto.bsq_taker_trade_fee,
            tx_fee_per_vbyte=proto.tx_fee_per_vbyte,
            maker_bsq_address=proto.maker_bsq_address,
            maker_btc_address=proto.maker_btc_address,
            taker_bsq_address=proto.taker_bsq_address,
            taker_btc_address=proto.taker_btc_address,
            num_confirmations=proto.num_confirmations,
            error_message=proto.error_message,
            payout=proto.payout,
            swap_peer_payout=proto.swap_peer_payout,
        )

    def __str__(self) -> str:
        return (
            f"BsqSwapTradeInfo{{"
            f"tx_id='{self.tx_id}', "
            f"bsq_trade_amount={self.bsq_trade_amount}, "
            f"btc_trade_amount={self.btc_trade_amount}, "
            f"bsq_maker_trade_fee={self.bsq_maker_trade_fee}, "
            f"bsq_taker_trade_fee={self.bsq_taker_trade_fee}, "
            f"tx_fee_per_vbyte={self.tx_fee_per_vbyte}, "
            f"maker_bsq_address='{self.maker_bsq_address}', "
            f"maker_btc_address='{self.maker_btc_address}', "
            f"taker_bsq_address='{self.taker_bsq_address}', "
            f"taker_btc_address='{self.taker_btc_address}', "
            f"num_confirmations={self.num_confirmations}, "
            f"error_message='{self.error_message}', "
            f"payout={self.payout}, "
            f"swap_peer_payout={self.swap_peer_payout}"
            f"}}"
        )
