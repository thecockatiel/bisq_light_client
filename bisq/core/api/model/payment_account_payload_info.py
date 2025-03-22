from typing import TYPE_CHECKING, Optional
from bisq.common.payload import Payload
from bisq.core.payment.payload.crypto_currency_account_payload import (
    CryptoCurrencyAccountPayload,
)
from bisq.core.payment.payload.instant_crypto_currency_account_payload import (
    InstantCryptoCurrencyPayload,
)
import grpc_pb2

if TYPE_CHECKING:
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload


class PaymentAccountPayloadInfo(Payload):
    def __init__(
        self,
        id: str,
        payment_method_id: str,
        address: Optional[str] = None,
        payment_details: Optional[str] = None,
    ):
        self.id = id
        self.payment_method_id = payment_method_id
        self.address = address
        self.payment_details = payment_details

    @staticmethod
    def from_payment_account_payload(
        payment_account_payload: "PaymentAccountPayload",
    ) -> "PaymentAccountPayloadInfo":
        if payment_account_payload is None:
            return None

        address = None
        if isinstance(
            payment_account_payload,
            (CryptoCurrencyAccountPayload, InstantCryptoCurrencyPayload),
        ):
            address = payment_account_payload.address

        pretty_payment_details = (
            payment_account_payload.get_payment_details_for_trade_popup()
        )
        payment_details = pretty_payment_details if pretty_payment_details else None

        return PaymentAccountPayloadInfo(
            payment_account_payload.id,
            payment_account_payload.payment_method_id,
            address,
            payment_details,
        )

    # For transmitting TradeInfo messages when the contract or the contract's payload is not yet available.
    @staticmethod
    def empty_payment_account_payload() -> "PaymentAccountPayloadInfo":
        return PaymentAccountPayloadInfo("", "", "", "")

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @staticmethod
    def from_proto(
        proto: grpc_pb2.PaymentAccountPayloadInfo,
    ) -> "PaymentAccountPayloadInfo":
        return PaymentAccountPayloadInfo(
            proto.id,
            proto.payment_method_id,
            proto.address,
            proto.payment_details,
        )

    def to_proto_message(self) -> grpc_pb2.PaymentAccountPayloadInfo:
        return grpc_pb2.PaymentAccountPayloadInfo(
            id=self.id,
            payment_method_id=self.payment_method_id,
            address=self.address if self.address is not None else "",
            payment_details=(
                self.payment_details if self.payment_details is not None else ""
            ),
        )
