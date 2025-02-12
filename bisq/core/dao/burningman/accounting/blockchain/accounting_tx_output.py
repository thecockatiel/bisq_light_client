from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.core.dao.burningman.burning_man_presentation_service import (
    BurningManPresentationService,
)
from bitcoinj.base.coin import Coin
import pb_pb2 as protobuf
from utils.preconditions import check_argument


# Outputs get pruned to required number of outputs depending on tx type.
# We store value as integer in protobuf as we do not support larger amounts than 21.47483647 BTC for our tx types.
# Name is burningman candidate name. For legacy Burningman we shorten to safe space.
class AccountingTxOutput(NetworkPayload):
    LEGACY_BM_FEES_SHORT = "LBMF"
    LEGACY_BM_DPT_SHORT = "LBMD"

    def __init__(self, value: int, name: str):
        self.value = value
        self.name = self.maybe_shorten_lbm(name)

    def maybe_shorten_lbm(self, name: str) -> str:
        return (
            AccountingTxOutput.LEGACY_BM_FEES_SHORT
            if name == BurningManPresentationService.LEGACY_BURNING_MAN_BTC_FEES_NAME
            else (
                AccountingTxOutput.LEGACY_BM_DPT_SHORT
                if name == BurningManPresentationService.LEGACY_BURNING_MAN_DPT_NAME
                else name
            )
        )

    def get_name(self) -> str:
        return (
            BurningManPresentationService.LEGACY_BURNING_MAN_BTC_FEES_NAME
            if self.name == AccountingTxOutput.LEGACY_BM_FEES_SHORT
            else (
                BurningManPresentationService.LEGACY_BURNING_MAN_DPT_NAME
                if self.name == AccountingTxOutput.LEGACY_BM_DPT_SHORT
                else self.name
            )
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self) -> protobuf.AccountingTxOutput:
        check_argument(
            self.value < 2147483647,
            "We only support integer value in protobuf storage for the amount and it need to be below 21.47483647 BTC",
        )
        return protobuf.AccountingTxOutput(value=self.value, name=self.name)

    @staticmethod
    def from_proto(proto: protobuf.AccountingTxOutput) -> "AccountingTxOutput":
        int_value = proto.value
        check_argument(int_value >= 0, "Value must not be negative")
        return AccountingTxOutput(int_value, proto.name)

    def __str__(self) -> str:
        return (
            f"AccountingTxOutput{{\n"
            f"                    value={self.value},\n"
            f"                    name='{self.name}'\n"
            f"}}"
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, AccountingTxOutput):
            return False
        return self.value == other.value and self.name == other.name

    def __hash__(self):
        return hash((self.value, self.name))
