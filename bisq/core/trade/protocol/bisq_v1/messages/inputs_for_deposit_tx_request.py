from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.btc.raw_transaction_input import RawTransactionInput
from bisq.common.crypto.sig import Sig
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.trade.protocol.trade_message import TradeMessage
from google.protobuf.message import Message
import proto.pb_pb2 as protobuf
from bisq.common.crypto.pub_key_ring import PubKeyRing
from bisq.core.network.p2p.node_address import NodeAddress

if TYPE_CHECKING:
    from bisq.core.protocol.core_proto_resolver import CoreProtoResolver

@dataclass(kw_only=True)
class InputsForDepositTxRequest(TradeMessage):
    sender_node_address: 'NodeAddress'
    trade_amount: int
    trade_price: int
    tx_fee: int
    taker_fee: int
    is_currency_for_taker_fee_btc: bool
    raw_transaction_inputs: List['RawTransactionInput']
    change_output_value: int
    
    change_output_address: Optional[str]
    taker_multi_sig_pub_key: bytes
    taker_payout_address_string: str
    taker_pub_key_ring: 'PubKeyRing'
    
    # Removed with 1.7.0
    taker_payment_account_payload: Optional['PaymentAccountPayload']
    
    taker_account_id: str
    taker_fee_tx_id: str
    accepted_arbitrator_node_addresses: List['NodeAddress']
    accepted_mediator_node_addresses: List['NodeAddress']
    accepted_refund_agent_node_addresses: List['NodeAddress']
    
    arbitrator_node_address: Optional['NodeAddress']
    mediator_node_address: 'NodeAddress'
    refund_agent_node_address: 'NodeAddress'
    
    account_age_witness_signature_of_offer_id: bytes
    current_date: int
    
    # Added at 1.7.0
    hash_of_takers_payment_account_payload: Optional[bytes]
    takers_payment_method_id: Optional[str]
    
    # Added in v 1.9.7
    burning_man_selection_height: int

    def to_proto_network_envelope(self) -> Message:
        message = protobuf.InputsForDepositTxRequest(
            trade_id=self.trade_id,
            sender_node_address=self.sender_node_address.to_proto_message(),
            trade_amount=self.trade_amount,
            trade_price=self.trade_price,
            tx_fee=self.tx_fee,
            taker_fee=self.taker_fee,
            is_currency_for_taker_fee_btc=self.is_currency_for_taker_fee_btc,
            raw_transaction_inputs=[input.to_proto_message() for input in self.raw_transaction_inputs],
            change_output_value=self.change_output_value,
            taker_multi_sig_pub_key=self.taker_multi_sig_pub_key,
            taker_payout_address_string=self.taker_payout_address_string,
            taker_pub_key_ring=self.taker_pub_key_ring.to_proto_message(),
            taker_account_id=self.taker_account_id,
            taker_fee_tx_id=self.taker_fee_tx_id,
            accepted_arbitrator_node_addresses=[addr.to_proto_message() for addr in self.accepted_arbitrator_node_addresses],
            accepted_mediator_node_addresses=[addr.to_proto_message() for addr in self.accepted_mediator_node_addresses],
            accepted_refund_agent_node_addresses=[addr.to_proto_message() for addr in self.accepted_refund_agent_node_addresses],
            mediator_node_address=self.mediator_node_address.to_proto_message(),
            refund_agent_node_address=self.refund_agent_node_address.to_proto_message(),
            uid=self.uid,
            account_age_witness_signature_of_offer_id=self.account_age_witness_signature_of_offer_id,
            current_date=self.current_date,
            burning_man_selection_height=self.burning_man_selection_height,   
        )

        if self.change_output_address:
            message.change_output_address = self.change_output_address
        if self.arbitrator_node_address:
            message.arbitrator_node_address.CopyFrom(self.arbitrator_node_address.to_proto_message())
        if self.taker_payment_account_payload:
            message.taker_payment_account_payload.CopyFrom(self.taker_payment_account_payload.to_proto_message())
        if self.hash_of_takers_payment_account_payload:
            message.hash_of_takers_payment_account_payload = self.hash_of_takers_payment_account_payload
        if self.takers_payment_method_id:
            message.takers_payout_method_id = self.takers_payment_method_id

        envelope = self.get_network_envelope_builder()
        envelope.inputs_for_deposit_tx_request.CopyFrom(message)
        
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.InputsForDepositTxRequest, core_proto_resolver: "CoreProtoResolver", message_version: int):
        raw_inputs = [RawTransactionInput.from_proto(input) for input in proto.raw_transaction_inputs]
        accepted_arbitrators = [NodeAddress.from_proto(addr) for addr in proto.accepted_arbitrator_node_addresses]
        accepted_mediators = [NodeAddress.from_proto(addr) for addr in proto.accepted_mediator_node_addresses]
        accepted_refund_agents = [NodeAddress.from_proto(addr) for addr in proto.accepted_refund_agent_node_addresses]

        taker_payment_payload = (
            core_proto_resolver.from_proto(proto.taker_payment_account_payload)
            if proto.HasField('taker_payment_account_payload') else None
        )
        
        hash_of_takers_payment = ProtoUtil.byte_array_or_none_from_proto(proto.hash_of_takers_payment_account_payload)

        return InputsForDepositTxRequest(
            trade_id=proto.trade_id,
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            trade_amount=proto.trade_amount,
            trade_price=proto.trade_price,
            tx_fee=proto.tx_fee,
            taker_fee=proto.taker_fee,
            is_currency_for_taker_fee_btc=proto.is_currency_for_taker_fee_btc,
            raw_transaction_inputs=raw_inputs,
            change_output_value=proto.change_output_value,
            change_output_address=ProtoUtil.string_or_none_from_proto(proto.change_output_address),
            taker_multi_sig_pub_key=proto.taker_multi_sig_pub_key,
            taker_payout_address_string=proto.taker_payout_address_string,
            taker_pub_key_ring=PubKeyRing.from_proto(proto.taker_pub_key_ring),
            taker_payment_account_payload=taker_payment_payload,
            taker_account_id=proto.taker_account_id,
            taker_fee_tx_id=proto.taker_fee_tx_id,
            accepted_arbitrator_node_addresses=accepted_arbitrators,
            accepted_mediator_node_addresses=accepted_mediators, 
            accepted_refund_agent_node_addresses=accepted_refund_agents,
            arbitrator_node_address=NodeAddress.from_proto(proto.arbitrator_node_address),
            mediator_node_address=NodeAddress.from_proto(proto.mediator_node_address),
            refund_agent_node_address=NodeAddress.from_proto(proto.refund_agent_node_address),
            uid=proto.uid,
            message_version=message_version,
            account_age_witness_signature_of_offer_id=proto.account_age_witness_signature_of_offer_id,
            current_date=proto.current_date,
            hash_of_takers_payment_account_payload=hash_of_takers_payment,
            takers_payment_method_id=ProtoUtil.string_or_none_from_proto(proto.takers_payout_method_id),
            burning_man_selection_height=proto.burning_man_selection_height,
        )
        
    def __str__(self):
        return (f"InputsForDepositTxRequest{{\n"
                f"     sender_node_address={self.sender_node_address},\n"
                f"     trade_amount={self.trade_amount},\n"
                f"     trade_price={self.trade_price},\n"
                f"     tx_fee={self.tx_fee},\n"
                f"     taker_fee={self.taker_fee},\n"
                f"     is_currency_for_taker_fee_btc={self.is_currency_for_taker_fee_btc},\n"
                f"     raw_transaction_inputs={self.raw_transaction_inputs},\n"
                f"     change_output_value={self.change_output_value},\n"
                f"     change_output_address='{self.change_output_address}',\n"
                f"     taker_multi_sig_pub_key={bytes_as_hex_string(self.taker_multi_sig_pub_key)},\n"
                f"     taker_payout_address_string='{self.taker_payout_address_string}',\n"
                f"     taker_pub_key_ring={self.taker_pub_key_ring},\n"
                f"     taker_account_id='{self.taker_account_id}',\n"
                f"     taker_fee_tx_id='{self.taker_fee_tx_id}',\n"
                f"     accepted_arbitrator_node_addresses={self.accepted_arbitrator_node_addresses},\n"
                f"     accepted_mediator_node_addresses={self.accepted_mediator_node_addresses},\n"
                f"     accepted_refund_agent_node_addresses={self.accepted_refund_agent_node_addresses},\n"
                f"     arbitrator_node_address={self.arbitrator_node_address},\n"
                f"     mediator_node_address={self.mediator_node_address},\n"
                f"     refund_agent_node_address={self.refund_agent_node_address},\n"
                f"     account_age_witness_signature_of_offer_id={bytes_as_hex_string(self.account_age_witness_signature_of_offer_id)},\n"
                f"     current_date={self.current_date},\n"
                f"     hash_of_takers_payment_account_payload={bytes_as_hex_string(self.hash_of_takers_payment_account_payload)},\n"
                f"     takers_payment_method_id={self.takers_payment_method_id},\n"
                f"     burning_man_selection_height={self.burning_man_selection_height}\n"
                f"}} {super().__str__()}")