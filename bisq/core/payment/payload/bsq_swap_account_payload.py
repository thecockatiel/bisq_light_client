from typing import Dict
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import proto.pb_pb2 as protobuf


class BsqSwapAccountPayload(PaymentAccountPayload):

    def __init__(self, payment_method_id: str, id: str):
        super().__init__(payment_method_id, id)

    def to_proto_message(self):
        payload = self.get_payment_account_payload_builder()
        payload.bsq_swap_account_payload.CopyFrom(protobuf.BsqSwapAccountPayload())
        return payload

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload) -> 'BsqSwapAccountPayload':
        return BsqSwapAccountPayload(proto.payment_method_id, proto.id)

    def get_payment_details(self) -> str:
        return "shared.na" # TODO: Res

    def get_payment_details_for_trade_popup(self) -> str:
        return self.get_payment_details()

    def get_age_witness_input_data(self) -> bytes:
        return super().get_age_witness_input_data_with_bytes(bytes())

