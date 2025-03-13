from bisq.common.proto import Proto
from bisq.core.dao.governance.consensus_critical import ConsensusCritical
from bisq.core.dao.state.model.governance.merit import Merit
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
import pb_pb2 as protobuf


class MeritList(Proto, ConsensusCritical, ImmutableDaoStateModel):

    def __init__(self, merit_list: list["Merit"]):
        self._list = merit_list

    @property
    def list(self) -> list["Merit"]:
        return self._list

    def to_proto_message(self) -> protobuf.MeritList:
        builder = protobuf.MeritList(
            merit=[merit.to_proto_message() for merit in self._list]
        )
        return builder

    @staticmethod
    def from_proto(proto: protobuf.MeritList) -> "MeritList":
        merit_list = [Merit.from_proto(merit_proto) for merit_proto in proto.merit]
        return MeritList(merit_list)

    @staticmethod
    def get_merit_list_from_bytes(byte_data: bytes) -> "MeritList":
        proto = protobuf.MeritList.FromString(byte_data)
        return MeritList.from_proto(proto)

    def __eq__(self, value):
        return isinstance(value, MeritList) and self._list == value._list

    def __hash__(self):
        # wrong but we do it anyway
        return hash(tuple(self._list))
