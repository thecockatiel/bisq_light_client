from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.dao.governance.consensus_critical import ConsensusCritical
from bisq.core.dao.state.model.governance.issuance import Issuance
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
import pb_pb2 as protobuf


class Merit(
    PersistablePayload, NetworkPayload, ConsensusCritical, ImmutableDaoStateModel
):

    def __init__(self, issuance: Issuance, signature: bytes):
        self._issuance = issuance
        self._signature = signature

    @property
    def issuance(self):
        return self._issuance

    @property
    def signature(self):
        return self._signature

    def to_proto_message(self):
        return protobuf.Merit(
            issuance=self._issuance.to_proto_message(),
            signature=self._signature,
        )

    @staticmethod
    def from_proto(proto: protobuf.Merit):
        return Merit(
            issuance=Issuance.from_proto(proto.issuance),
            signature=proto.signature,
        )

    @property
    def issuance_tx_id(self):
        return self._issuance.tx_id

    def __str__(self):
        return (
            f"Merit{{\n"
            f"     issuance={self.issuance},\n"
            f"     signature={bytes_as_hex_string(self.signature)}\n"
            f"}}"
        )
