from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.dao.governance.consensus_critical import ConsensusCritical
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
import pb_pb2 as protobuf


class Vote(
    PersistablePayload, NetworkPayload, ConsensusCritical, ImmutableDaoStateModel
):

    def __init__(self, accepted: bool):
        self.accepted = accepted

    def to_proto_message(self):
        return protobuf.Vote(accepted=self.accepted)

    @staticmethod
    def from_proto(proto: protobuf.Vote):
        return Vote(proto.accepted)
