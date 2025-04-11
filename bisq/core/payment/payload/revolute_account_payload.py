from typing import Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf
from utils.preconditions import check_argument


class RevolutAccountPayload(PaymentAccountPayload):

    def __init__(
        self,
        payment_method_id: str,
        id: str,
        account_id: str = "",
        user_name: Optional[str] = "",
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_id, id, max_trade_period, exclude_from_json_data_map
        )

        # Only used as internal Id to not break existing account witness objects
        # We still show it in case it is different to the userName for additional security
        self.account_id = account_id
        # Was added in 1.3.8
        # To not break signed accounts we keep accountId as internal id used for signing.
        # Old accounts get a popup to add the new required field userName but accountId is
        # left unchanged. Newly created accounts fill accountId with the value of userName.
        # In the UI we only use userName.

        # For backward compatibility we need to exclude the new field for the contract json.
        # We can remove that after a while when risk that users with pre 1.3.8 version trade with updated
        # users is very low.
        self.user_name = user_name

    def get_json_dict(self):
        result = super().get_json_dict()
        result.pop("userName", None)
        return result

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self):
        revolut = protobuf.RevolutAccountPayload(
            account_id=self.account_id,
            user_name=self.user_name,
        )
        builder = self.get_payment_account_payload_builder()
        builder.revolut_account_payload.CopyFrom(revolut)
        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload):
        revolut_account_payload = proto.revolut_account_payload
        return RevolutAccountPayload(
            payment_method_id=proto.payment_method_id,
            id=proto.id,
            account_id=revolut_account_payload.account_id,
            user_name=revolut_account_payload.user_name,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=ProtoUtil.to_string_map(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        tuple = self.get_label_value_tuple()
        return f"{Res.get(self.payment_method_id)} - {tuple[0]}: {tuple[1]}"

    def get_label_value_tuple(self) -> tuple[str, str]:
        check_argument(
            self.user_name or self.has_old_account_id,
            "Either username must be set or we have an old account with accountId",
        )

        if self.user_name:
            label = Res.get("payment.account.userName")
            value = self.user_name

            if self.has_old_account_id:
                label += "/" + Res.get("payment.account.phoneNr")
                value += "/" + self.account_id
        else:
            label = Res.get("payment.account.phoneNr")
            value = self.account_id

        return label, value

    def get_recipients_account_data(self) -> tuple[str, str]:
        tuple_data = self.get_label_value_tuple()
        label = Res.get(
            "portfolio.pending.step2_buyer.recipientsAccountData", tuple_data[0]
        )
        return label, tuple_data[1]

    def get_payment_details_for_trade_popup(self) -> str:
        return self.get_payment_details()

    def get_age_witness_input_data(self) -> bytes:
        # getAgeWitnessInputData is called at new account creation when accountId is empty string.
        if self.has_old_account_id:
            # If the accountId was already in place (updated user who had used accountId for account age) we keep the
            # old accountId to not invalidate the existing account age witness.
            return self.get_age_witness_input_data_using_bytes(
                self.account_id.encode("utf-8")
            )
        # If a new account was registered from version 1.3.8 or later we use the userName.
        return self.get_age_witness_input_data_using_bytes(
            self.user_name.encode("utf-8")
        )

    @property
    def user_name_not_set(self) -> bool:
        return not bool(self.user_name)

    @property
    def has_old_account_id(self) -> bool:
        return self.account_id != self.user_name

    # In case it is a new account we need to fill the accountId field to support not-updated traders who are not
    # aware of the new userName field
    def maybe_apply_user_name_to_account_id(self) -> None:
        if not self.account_id:
            self.account_id = self.user_name
