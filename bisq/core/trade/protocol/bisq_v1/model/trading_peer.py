from typing import TYPE_CHECKING, Optional

from bisq.common.crypto.pub_key_ring import PubKeyRing
from bisq.common.protocol.proto_util import ProtoUtil
import proto.pb_pb2 as protobuf
from bisq.core.trade.protocol.trade_peer import TradePeer
from bisq.core.btc.raw_transaction_input import RawTransactionInput

if TYPE_CHECKING:
    from bisq.core.protocol.core_proto_resolver import CoreProtoResolver
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload

# Fields marked as transient are only used during protocol execution which are based on directMessages so we do not
# persist them.
# todo clean up older fields as well to make most transient
class TradingPeer(TradePeer):
    def __init__(self):
        super().__init__()
        # Transient/Mutable
        # Added in v1.2.0
        self.delayed_payout_tx_signature: Optional[bytes] = None
        self.prepared_deposit_tx: Optional[bytes] = None

        # Persistable mutable
        self.account_id: Optional[str] = None
        self.payment_account_payload: Optional['PaymentAccountPayload'] = None
        self.payout_address_string: Optional[str] = None
        self.contract_as_json: Optional[str] = None
        self.contract_signature: Optional[str] = None
        self.signature: Optional[bytes] = None
        self.pub_key_ring: Optional['PubKeyRing'] = None
        self.multi_sig_pub_key: Optional[bytes] = None
        self.raw_transaction_inputs: Optional[list['RawTransactionInput']] = None
        self.change_output_value: int = 0
        self.change_output_address: Optional[str] = None

        # Added in v0.6
        self.account_age_witness_nonce: Optional[bytes] = None
        self.account_age_witness_signature: Optional[bytes] = None
        self.current_date: int = 0

        # Added in v1.1.6
        self.mediated_payout_tx_signature: Optional[bytes] = None

        # Added in v1.7.0
        self.hash_of_payment_account_payload: Optional[bytes] = None
        self.payment_method_id: Optional[str] = None

    def to_proto_message(self):
        trading_peer = protobuf.TradingPeer(
            change_output_value=self.change_output_value,
            account_id=self.account_id,
            payment_account_payload=self.payment_account_payload.to_proto_message() if self.payment_account_payload else None,
            payout_address_string=self.payout_address_string,
            contract_as_json=self.contract_as_json,
            contract_signature=self.contract_signature,
            signature=self.signature,
            pub_key_ring= self.pub_key_ring.to_proto_message() if self.pub_key_ring else None,
            multi_sig_pub_key=self.multi_sig_pub_key,
            raw_transaction_inputs=ProtoUtil.collection_to_proto(self.raw_transaction_inputs, protobuf.RawTransactionInput) if self.raw_transaction_inputs else None,
            change_output_address=self.change_output_address,
            account_age_witness_nonce=self.account_age_witness_nonce,
            account_age_witness_signature=self.account_age_witness_signature,
            mediated_payout_tx_signature=self.mediated_payout_tx_signature,
            hash_of_payment_account_payload=self.hash_of_payment_account_payload,
            current_date=self.current_date,
        )
        return trading_peer
    
    @staticmethod
    def from_proto(proto: protobuf.TradingPeer, core_proto_resolver: "CoreProtoResolver"):
        if not proto.ListFields():
            return None
        trading_peer = TradingPeer()
        trading_peer.change_output_value = proto.change_output_value
        trading_peer.account_id = proto.account_id
        trading_peer.payment_account_payload = core_proto_resolver.from_proto(proto.payment_account_payload) if proto.HasField("payment_account_payload") else None
        trading_peer.payout_address_string = ProtoUtil.string_or_none_from_proto(proto.payout_address_string)
        trading_peer.contract_as_json = ProtoUtil.string_or_none_from_proto(proto.contract_as_json)
        trading_peer.contract_signature = ProtoUtil.string_or_none_from_proto(proto.contract_signature)
        trading_peer.signature = ProtoUtil.byte_array_or_none_from_proto(proto.signature)
        trading_peer.pub_key_ring = PubKeyRing.from_proto(proto.pub_key_ring) if proto.HasField("pub_key_ring") else None
        trading_peer.multi_sig_pub_key = ProtoUtil.byte_array_or_none_from_proto(proto.multi_sig_pub_key)
        trading_peer.raw_transaction_inputs = [RawTransactionInput.from_proto(input) for input in proto.raw_transaction_inputs] if proto.HasField("raw_transaction_inputs") else None
        trading_peer.change_output_address = ProtoUtil.string_or_none_from_proto(proto.change_output_address)
        trading_peer.account_age_witness_nonce = ProtoUtil.byte_array_or_none_from_proto(proto.account_age_witness_nonce)
        trading_peer.account_age_witness_signature = ProtoUtil.byte_array_or_none_from_proto(proto.account_age_witness_signature)
        trading_peer.current_date = proto.current_date
        trading_peer.mediated_payout_tx_signature = ProtoUtil.byte_array_or_none_from_proto(proto.mediated_payout_tx_signature)
        trading_peer.hash_of_payment_account_payload = ProtoUtil.byte_array_or_none_from_proto(proto.hash_of_payment_account_payload)
        return trading_peer