from enum import IntEnum
import pb_pb2 as protobuf
from bisq.common.protocol.proto_util import ProtoUtil

class OpenOfferState(IntEnum):
    AVAILABLE = 0
    RESERVED = 1
    CLOSED = 2
    CANCELED = 3
    DEACTIVATED = 4
    
    @staticmethod
    def from_proto(state: protobuf.OpenOffer.State) -> "OpenOfferState":
        return ProtoUtil.enum_from_proto(OpenOfferState, protobuf.OpenOffer.State, state)

    @staticmethod
    def to_proto_message(state: "OpenOfferState"):
        return ProtoUtil.proto_enum_from_enum(protobuf.OpenOffer.State, state)

