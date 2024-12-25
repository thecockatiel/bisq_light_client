from abc import ABC, abstractmethod
from typing import Optional
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import proto.pb_pb2 as protobuf


class CountryBasedPaymentAccountPayload(PaymentAccountPayload, ABC):
    def __init__(
        self,
        payment_method_name: str,
        id: str,
        country_code: str,
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_name, id, max_trade_period, exclude_from_json_data_map
        )
        self._country_code = country_code
    
    @property
    def country_code(self) -> str:
        return self._country_code
    
    @country_code.setter
    def country_code(self, country_code: str):
        self._country_code = country_code

    def get_payment_account_payload_builder(self):
        country_payload = protobuf.CountryBasedPaymentAccountPayload(
            countryCode=self.country_code
        )
        payload = super().get_payment_account_payload_builder()
        payload.country_based_payment_account_payload.CopyFrom(country_payload)
        return payload

    @abstractmethod
    def get_payment_details(self) -> str:
        pass

    @abstractmethod
    def get_payment_details_for_trade_popup(self) -> str:
        pass

    def get_age_witness_input_data(self, data: bytes) -> bytes:
        country_code_bytes = self.country_code.encode("utf-8")
        return self.get_age_witness_input_data_using_bytes(country_code_bytes + data)
