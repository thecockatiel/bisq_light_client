from enum import IntEnum
from bisq.common.protocol.proto_util import ProtoUtil
import pb_pb2 as protobuf

class SignedWitnessVerificationMethod(IntEnum):
    ARBITRATOR = 0
    TRADE = 1

    @staticmethod
    def from_proto(proto: protobuf.SignedWitness.VerificationMethod):
        return ProtoUtil.enum_from_proto(SignedWitnessVerificationMethod, protobuf.SignedWitness.VerificationMethod, proto)

    @staticmethod
    def to_proto_message(method: "SignedWitnessVerificationMethod"):
        return ProtoUtil.proto_enum_from_enum(protobuf.SignedWitness.VerificationMethod, method)