from typing import Optional
from bisq.core.payment.payload.assets_account_payload import AssetsAccountPayload
import pb_pb2 as protobuf


class InstantCryptoCurrencyPayload(AssetsAccountPayload):

    def __init__(
        self,
        payment_method_id: str,
        id: str,
        address: str = None,
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_id, id, max_trade_period, exclude_from_json_data_map
        )
        self.address = address or ""

    def to_proto_message(self):
        builder = self.get_payment_account_payload_builder()
        builder.instant_crypto_currency_account_payload.CopyFrom(
            protobuf.InstantCryptoCurrencyAccountPayload(address=self.address)
        )
        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload):
        return InstantCryptoCurrencyPayload(
            proto.payment_method_id,
            proto.id,
            proto.crypto_currency_account_payload.address,
            proto.max_trade_period,
            dict(proto.exclude_from_json_data),
        )
