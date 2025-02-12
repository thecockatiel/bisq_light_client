from enum import Enum
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
import pb_pb2 as protobuf


class ScriptType(ImmutableDaoStateModel, Enum):
    UNDEFINED = "undefined"
    # https://github.com/bitcoin/bitcoin/blob/master/src/script/standard.cpp
    NONSTANDARD = "nonstandard"
    PUB_KEY = "pubkey"
    PUB_KEY_HASH = "pubkeyhash"
    SCRIPT_HASH = "scripthash"
    MULTISIG = "multisig"
    NULL_DATA = "nulldata"
    WITNESS_V0_KEYHASH = "witness_v0_keyhash"
    WITNESS_V0_SCRIPTHASH = "witness_v0_scripthash"
    WITNESS_V1_TAPROOT = "witness_v1_taproot"
    WITNESS_UNKNOWN = "witness_unknown"

    def __init__(self, json_name: str):
        self.json_name = json_name

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    @staticmethod
    def from_json_name(json_name: str):
        for script_type in ScriptType:
            if script_type.json_name == json_name:
                return script_type
        raise IllegalArgumentException(
            "Expected the argument to be a valid 'bitcoind' script type, "
            "but was invalid/unsupported instead. Received scriptType=" + json_name
        )

    def to_proto_message(self):
        return ProtoUtil.proto_enum_from_enum(protobuf.ScriptType, self)

    @staticmethod
    def from_proto(proto: protobuf.ScriptType):
        return ProtoUtil.enum_from_proto(ScriptType, protobuf.ScriptType, proto)
