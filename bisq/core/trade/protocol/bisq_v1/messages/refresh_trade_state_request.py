from dataclasses import dataclass
 
from bisq.core.network.p2p.node_address import NodeAddress 
from bisq.core.trade.protocol.bisq_v1.messages.trade_mailbox_message import TradeMailboxMessage
import proto.pb_pb2 as protobuf

@dataclass(frozen=True, kw_only=True)
class RefreshTradeStateRequest(TradeMailboxMessage):
    """
    Not used anymore since v1.4.0
    We do the re-sending of the payment sent message via the BuyerSendCounterCurrencyTransferStartedMessage task on the
    buyer side, so seller do not need to do anything interactively.
    """
    sender_node_address: NodeAddress

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        request = protobuf.RefreshTradeStateRequest(
            uid=self.uid,
            trade_id=self.trade_id,
            sender_node_address=self.sender_node_address.to_proto_message()
        )
        envelope = self.get_network_envelope_builder()
        envelope.refresh_trade_state_request.CopyFrom(request)
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.RefreshTradeStateRequest, message_version: int) -> 'RefreshTradeStateRequest':
        return RefreshTradeStateRequest(
            message_version=message_version,
            uid=proto.uid,
            trade_id=proto.trade_id,
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address)
        )