from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
import proto.pb_pb2 as protobuf


class ParamChange(PersistablePayload, ImmutableDaoStateModel):
    """
    Holds the data for a parameter change. Gets persisted with the DaoState.
    """

    # We use the enum name instead of the enum to be more flexible with changes at updates
    def __init__(self, param_name: str, value: str, activation_height: int):
        self.param_name = param_name
        self.value = value
        self.activation_height = activation_height

    def to_proto_message(self):
        return protobuf.ParamChange(
            param_name=self.param_name,
            param_value=self.value,
            activation_height=self.activation_height,
        )

    @staticmethod
    def from_proto(self, proto: protobuf.ParamChange):
        return ParamChange(
            param_name=proto.param_name,
            value=proto.param_value,
            activation_height=proto.activation_height,
        )
