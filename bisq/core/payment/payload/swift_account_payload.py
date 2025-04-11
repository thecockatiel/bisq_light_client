from typing import Union
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf

class SwiftAccountPayload(PaymentAccountPayload):
    # Class constants
    BANKPOSTFIX = ".bank"
    INTERMEDIARYPOSTFIX = ".intermediary"
    BENEFICIARYPOSTFIX = ".beneficiary"
    SWIFT_CODE = "payment.swift.swiftCode"
    COUNTRY = "payment.swift.country"
    SWIFT_ACCOUNT = "payment.swift.account"
    SNAME = "payment.swift.name"
    BRANCH = "payment.swift.branch"
    ADDRESS = "payment.swift.address"
    PHONE = "payment.swift.phone"

    def __init__(self, payment_method: str, id: str, bank_swift_code: str = "", bank_country_code: str = "",
               bank_name: str = "", bank_branch: str = "", bank_address: str = "", beneficiary_name: str = "",
               beneficiary_account_nr: str = "", beneficiary_address: str = "", beneficiary_city: str = "",
               beneficiary_phone: str = "", special_instructions: str = "", intermediary_swift_code: str = "",
               intermediary_country_code: str = "", intermediary_name: str = "", intermediary_branch: str = "",
               intermediary_address: str = "", max_trade_period: int = -1,
               exclude_from_json_data_map: Union[dict[str, str]] = None):
        super().__init__(payment_method, id, max_trade_period, exclude_from_json_data_map)
        # Initialize payload data elements
        self.bank_swift_code = bank_swift_code
        self.bank_country_code = bank_country_code
        self.bank_name = bank_name
        self.bank_branch = bank_branch
        self.bank_address = bank_address
        self.beneficiary_name = beneficiary_name
        self.beneficiary_account_nr = beneficiary_account_nr
        self.beneficiary_address = beneficiary_address
        self.beneficiary_city = beneficiary_city
        self.beneficiary_phone = beneficiary_phone
        self.special_instructions = special_instructions
        self.intermediary_swift_code = intermediary_swift_code
        self.intermediary_country_code = intermediary_country_code
        self.intermediary_name = intermediary_name
        self.intermediary_branch = intermediary_branch
        self.intermediary_address = intermediary_address
        

    def to_proto_message(self):
        builder = self.get_payment_account_payload_builder()
        builder.swift_account_payload.CopyFrom(protobuf.SwiftAccountPayload(
            bank_swift_code=self.bank_swift_code,
            bank_country_code=self.bank_country_code,
            bank_name=self.bank_name,
            bank_branch=self.bank_branch,
            bank_address=self.bank_address,
            beneficiary_name=self.beneficiary_name,
            beneficiary_account_nr=self.beneficiary_account_nr,
            beneficiary_address=self.beneficiary_address,
            beneficiary_city=self.beneficiary_city,
            beneficiary_phone=self.beneficiary_phone,
            special_instructions=self.special_instructions,
            intermediary_swift_code=self.intermediary_swift_code,
            intermediary_country_code=self.intermediary_country_code,
            intermediary_name=self.intermediary_name,
            intermediary_branch=self.intermediary_branch,
            intermediary_address=self.intermediary_address,
        ))
        return builder
    
    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload) -> "SwiftAccountPayload":
        x = proto.swift_account_payload
        return SwiftAccountPayload(
            payment_method=proto.payment_method_id,
            id=proto.id,
            bank_swift_code=x.bank_swift_code,
            bank_country_code=x.bank_country_code,
            bank_name=x.bank_name,
            bank_branch=x.bank_branch,
            bank_address=x.bank_address,
            beneficiary_name=x.beneficiary_name,
            beneficiary_account_nr=x.beneficiary_account_nr,
            beneficiary_address=x.beneficiary_address,
            beneficiary_city=x.beneficiary_city,
            beneficiary_phone=x.beneficiary_phone,
            special_instructions=x.special_instructions,
            intermediary_swift_code=x.intermediary_swift_code,
            intermediary_country_code=x.intermediary_country_code,
            intermediary_name=x.intermediary_name,
            intermediary_branch=x.intermediary_branch,
            intermediary_address=x.intermediary_address,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=ProtoUtil.to_string_map(proto.exclude_from_json_data)
        )

    def get_payment_details(self) -> str:
        method = Res.get("self.payment_method_id")
        return f"{method} - {self.beneficiary_name}"

    def get_payment_details_for_trade_popup(self) -> str:
        return self.get_payment_details()

    def get_age_witness_input_data(self) -> bytes:
        return self.get_age_witness_input_data_using_bytes(self.beneficiary_account_nr.encode('utf-8'))

    def uses_intermediary_bank(self) -> bool:
        return bool(self.intermediary_swift_code and len(self.intermediary_swift_code) > 0)

