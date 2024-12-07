from enum import IntEnum
import proto.pb_pb2 as protobuf
from bisq.common.protocol.proto_util import ProtoUtil


class AddressEntryContext(IntEnum):
    ARBITRATOR = 0
    AVAILABLE = 1
    OFFER_FUNDING = 2
    RESERVED_FOR_TRADE = 3
    MULTI_SIG = 4
    TRADE_PAYOUT = 5

    @staticmethod
    def from_proto(value: protobuf.AddressEntry.Context) -> "AddressEntryContext":
        return ProtoUtil.enum_from_proto(
            AddressEntryContext, protobuf.AddressEntry.Context, value
        )

    @staticmethod
    def to_proto_message(value: "AddressEntryContext"):
        return ProtoUtil.proto_enum_from_enum(protobuf.AddressEntry.Context, value)

