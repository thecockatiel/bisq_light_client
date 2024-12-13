from abc import ABC

from bisq.common.crypto.pub_key_ring import PubKeyRing
from bisq.core.network.p2p.direct_message import DirectMessage
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.trade.protocol.trade_message import TradeMessage


class BsqSwapRequest(TradeMessage, DirectMessage, ABC):
    def __init__(self, 
                 message_version: int,
                 trade_id: str,
                 uid: str,
                 sender_node_address: NodeAddress,
                 taker_pub_key_ring: PubKeyRing,
                 trade_amount: int,
                 tx_fee_per_vbyte: int,
                 maker_fee: int,
                 taker_fee: int,
                 trade_date: int):
        super().__init__(message_version=message_version, trade_id=trade_id, uid=uid)
        self.sender_node_address = sender_node_address
        self.taker_pub_key_ring = taker_pub_key_ring
        self.trade_amount = trade_amount
        self.tx_fee_per_vbyte = tx_fee_per_vbyte
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.trade_date = trade_date
