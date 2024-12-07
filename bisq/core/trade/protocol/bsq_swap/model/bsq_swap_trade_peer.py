from typing import Optional
from bisq.common.crypto.pub_key_ring import PubKeyRing
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.btc.raw_transaction_input import RawTransactionInput
from bisq.core.trade.protocol.trade_peer import TradePeer
import proto.pb_pb2 as protobuf

class BsqSwapTradePeer(TradePeer):
    
    def __init__(self):
        super().__init__()
        self.pub_key_ring: Optional["PubKeyRing"] = None
        self.btc_address: Optional[str] = None
        self.bsq_address: Optional[str] = None
        
        self.inputs: Optional[list["RawTransactionInput"]] = None
        self.change = 0
        self.payout = 0
        self.tx: Optional[bytes] = None
    
    def get_pub_key_ring(self):
        return self.pub_key_ring
    
    def set_pub_key_ring(self, pub_key_ring: "PubKeyRing"):
        self.pub_key_ring = pub_key_ring

    def to_proto_message(self) -> protobuf.BsqSwapTradePeer:
        builder = protobuf.BsqSwapTradePeer(
            change=self.change,
            payout=self.payout
        )
        
        if self.pub_key_ring:
            builder.pub_key_ring.CopyFrom(self.pub_key_ring.to_proto_message())
        if self.btc_address:
            builder.btc_address = self.btc_address
        if self.bsq_address:
            builder.bsq_address = self.bsq_address
        if self.inputs:
            builder.inputs.extend([input.to_proto_message() for input in self.inputs])
        if self.tx:
            builder.tx = self.tx
            
        return builder

    @staticmethod
    def from_proto(proto: protobuf.BsqSwapTradePeer) -> Optional["BsqSwapTradePeer"]:
        if proto == protobuf.BsqSwapTradePeer():
            return None
            
        bsq_swap_trade_peer = BsqSwapTradePeer()
        bsq_swap_trade_peer.pub_key_ring = PubKeyRing.from_proto(proto.pub_key_ring) if proto.HasField('pub_key_ring') else None
        bsq_swap_trade_peer.change = proto.change
        bsq_swap_trade_peer.payout = proto.payout
        bsq_swap_trade_peer.btc_address = proto.btc_address
        bsq_swap_trade_peer.bsq_address = proto.bsq_address
        
        inputs = [RawTransactionInput.from_proto(input) for input in proto.inputs] if proto.inputs else None
        bsq_swap_trade_peer.inputs = inputs
        bsq_swap_trade_peer.tx = ProtoUtil.byte_array_or_none_from_proto(proto.tx)
        
        return bsq_swap_trade_peer

    def __str__(self) -> str:
        return (f"BsqSwapTradePeer{{\n"
                f"     pubKeyRing={self.pub_key_ring},\n"
                f"     btcAddress='{self.btc_address}',\n"
                f"     bsqAddress='{self.bsq_address}',\n"
                f"     inputs={self.inputs},\n"
                f"     change={self.change},\n"
                f"     payout={self.payout},\n"
                f"     tx={bytes_as_hex_string(self.tx)}\n"
                "}")
