from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.btc.raw_transaction_input import RawTransactionInput
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.network.p2p.direct_message import DirectMessage
from bisq.core.network.p2p.network.core_proto_resolver import CoreProtoResolver
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.trade.protocol.trade_message import TradeMessage
import proto.pb_pb2 as protobuf


@dataclass(kw_only=True)
class InputsForDepositTxResponse(TradeMessage, DirectMessage):
    # Removed with 1.7.0
    maker_payment_account_payload: Optional[PaymentAccountPayload]

    maker_account_id: str
    maker_multi_sig_pub_key: bytes
    maker_contract_as_json: str
    maker_contract_signature: str
    maker_payout_address_string: str
    prepared_deposit_tx: bytes
    maker_inputs: List['RawTransactionInput']
    sender_node_address: NodeAddress

    # added in v 0.6. can be null if we trade with an older peer
    account_age_witness_signature_of_prepared_deposit_tx: Optional[bytes]
    current_date: int
    lock_time: int

    # Added at 1.7.0
    hash_of_makers_payment_account_payload: Optional[bytes]
    makers_payment_method_id: Optional[str]

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        message = protobuf.InputsForDepositTxResponse(
            trade_id=self.trade_id,
            maker_account_id=self.maker_account_id,
            maker_multi_sig_pub_key=self.maker_multi_sig_pub_key,
            maker_contract_as_json=self.maker_contract_as_json,
            maker_contract_signature=self.maker_contract_signature,
            maker_payout_address_string=self.maker_payout_address_string,
            prepared_deposit_tx=self.prepared_deposit_tx,
            maker_inputs=[input.to_proto_message() for input in self.maker_inputs],
            sender_node_address=self.sender_node_address.to_proto_message(),
            uid=self.uid,
            lock_time=self.lock_time,
            current_date=self.current_date,
        )

        if self.account_age_witness_signature_of_prepared_deposit_tx:
            message.account_age_witness_signature_of_prepared_deposit_tx = (
                self.account_age_witness_signature_of_prepared_deposit_tx
            )

        if self.maker_payment_account_payload:
            message.maker_payment_account_payload.CopyFrom(
                self.maker_payment_account_payload.to_proto_message()
            )

        if self.hash_of_makers_payment_account_payload:
            message.hash_of_makers_payment_account_payload = (
                self.hash_of_makers_payment_account_payload
            )

        if self.makers_payment_method_id:
            message.makers_payout_method_id = self.makers_payment_method_id

        envelope = self.get_network_envelope_builder()
        envelope.inputs_for_deposit_tx_response.CopyFrom(message)
        return envelope

    @staticmethod
    def from_proto(
        proto: protobuf.InputsForDepositTxResponse,
        core_proto_resolver: CoreProtoResolver,
        message_version: int,
    ):
        maker_inputs = [
            RawTransactionInput.from_proto(input) for input in proto.maker_inputs
        ]

        maker_payment_account_payload = (
            core_proto_resolver.from_proto(proto.maker_payment_account_payload)
            if proto.HasField("maker_payment_account_payload")
            else None
        )

        return InputsForDepositTxResponse(
            trade_id=proto.trade_id,
            maker_payment_account_payload=maker_payment_account_payload,
            maker_account_id=proto.maker_account_id,
            maker_multi_sig_pub_key=proto.maker_multi_sig_pub_key,
            maker_contract_as_json=proto.maker_contract_as_json,
            maker_contract_signature=proto.maker_contract_signature,
            maker_payout_address_string=proto.maker_payout_address_string,
            prepared_deposit_tx=proto.prepared_deposit_tx,
            maker_inputs=maker_inputs,
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            uid=proto.uid,
            message_version=message_version,
            account_age_witness_signature_of_prepared_deposit_tx=ProtoUtil.byte_array_or_none_from_proto(proto.account_age_witness_signature_of_prepared_deposit_tx),
            current_date=proto.current_date,
            lock_time=proto.lock_time,
            hash_of_makers_payment_account_payload=ProtoUtil.byte_array_or_none_from_proto(proto.hash_of_makers_payment_account_payload),
            makers_payment_method_id=ProtoUtil.string_or_none_from_proto(proto.makers_payout_method_id),
        )

    def __str__(self) -> str:
        return (
            f"InputsForDepositTxResponse(\n"
            f"    maker_account_id='{self.maker_account_id}',\n"
            f"    maker_multi_sig_pub_key={bytes_as_hex_string(self.maker_multi_sig_pub_key)},\n"
            f"    maker_contract_as_json='{self.maker_contract_as_json}',\n"
            f"    maker_contract_signature='{self.maker_contract_signature}',\n"
            f"    maker_payout_address_string='{self.maker_payout_address_string}',\n"
            f"    prepared_deposit_tx={bytes_as_hex_string(self.prepared_deposit_tx)},\n"
            f"    maker_inputs={self.maker_inputs},\n"
            f"    sender_node_address={self.sender_node_address},\n"
            f"    account_age_witness_signature={bytes_as_hex_string(self.account_age_witness_signature_of_prepared_deposit_tx)},\n"
            f"    current_date={datetime.fromtimestamp(self.current_date/1000)},\n"
            f"    lock_time={self.lock_time},\n"
            f"    hash_of_makers_payment_account_payload={bytes_as_hex_string(self.hash_of_makers_payment_account_payload)},\n"
            f"    makers_payment_method_id={self.makers_payment_method_id}\n"
            f") {super().__str__()}"
        )
