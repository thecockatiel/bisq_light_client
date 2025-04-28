from dataclasses import dataclass
from bisq.common.protocol.network.network_payload import NetworkPayload
import pb_pb2 as protobuf


@dataclass(frozen=True)
class PaymentAccountFilter(NetworkPayload):
    payment_method_id: str
    get_method_name: str
    value: str

    def to_proto_message(self) -> protobuf.PaymentAccountFilter:
        return protobuf.PaymentAccountFilter(
            payment_method_id=self.payment_method_id,
            get_method_name=self.get_method_name,
            value=self.value,
        )

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountFilter):
        return PaymentAccountFilter(
            payment_method_id=proto.payment_method_id,
            get_method_name=proto.get_method_name,
            value=proto.value,
        )

    def __repr__(self):
        return (
            f"PaymentAccountFilter("
            f"payment_method_id='{self.payment_method_id}', "
            f"get_method_name='{self.get_method_name}', "
            f"value='[HIDDEN]')"
        )
