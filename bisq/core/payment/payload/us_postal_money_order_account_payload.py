from typing import Optional
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payload_with_holder_name import PayloadWithHolderName
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf


class USPostalMoneyOrderAccountPayload(PaymentAccountPayload, PayloadWithHolderName):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        postal_address: str = "",
        holder_name: str = "",
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_name,
            id,
            max_trade_period,
            exclude_from_json_data_map,
        )
        self.postal_address = postal_address
        self._holder_name = holder_name

    @property
    def holder_name(self):
        return self._holder_name
    
    @holder_name.setter
    def holder_name(self, value: str):
        self._holder_name = value

    def to_proto_message(self):
        payload = protobuf.USPostalMoneyOrderAccountPayload(
            postal_address=self.postal_address,
            holder_name=self.holder_name,
        )

        builder = self.get_payment_account_payload_builder()
        builder.u_s_postal_money_order_account_payload.CopyFrom(payload)

        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.PaymentAccountPayload,
    ) -> "USPostalMoneyOrderAccountPayload":
        payload = proto.u_s_postal_money_order_account_payload

        return USPostalMoneyOrderAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            postal_address=payload.postal_address,
            holder_name=payload.holder_name,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        payment_method = Res.get(self.payment_method_id)
        owner = Res.get_with_col("payment.account.owner")
        postal_address = Res.get_with_col("payment.postal.address")
        return f"{payment_method} - {owner} {self.holder_name}, {postal_address} {self.postal_address}"

    def get_payment_details_for_trade_popup(self) -> str:
        return (
            f"{Res.get_with_col('payment.account.owner')} {self.holder_name}\n"
            f"{Res.get_with_col('payment.postal.address')} {self.postal_address}"
        )

    def get_age_witness_input_data(self) -> bytes:
        # We use here the contact because the address alone seems to be too weak
        holder_bytes = self.holder_name.encode("utf-8")
        address_bytes = self.postal_address.encode("utf-8")
        return self.get_age_witness_input_data_using_bytes(holder_bytes + address_bytes)

    @property
    def owner_id(self) -> str:
        return self.holder_name
