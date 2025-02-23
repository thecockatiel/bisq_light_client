from typing import Optional
from bisq.common.protocol.persistable.persistable_envelope import PersistableEnvelope

from bisq.core.dao.monitoring.model.dao_state_hash import DaoStateHash
import pb_pb2 as protobuf


class DaoStateStore(PersistableEnvelope):

    def __init__(
        self,
        dao_state_as_proto: Optional[protobuf.DaoState],
        dao_state_hash_chain: list[DaoStateHash],
    ):
        self.dao_state_as_proto = dao_state_as_proto
        self.dao_state_hash_chain: Optional[list[DaoStateHash]] = dao_state_hash_chain

    def to_proto_message(self):
        assert (
            self.dao_state_as_proto is not None
        ), "dao_state_as_proto must not be None when to_proto_message is invoked"
        assert (
            self.dao_state_hash_chain is not None
        ), "dao_state_hash_chain must not be None when to_proto_message is invoked"
        return protobuf.PersistableEnvelope(
            dao_state_store=protobuf.DaoStateStore(
                dao_state=self.dao_state_as_proto,
                dao_state_hash=[
                    dao_state_hash.to_proto_message()
                    for dao_state_hash in self.dao_state_hash_chain
                ],
            )
        )

    @staticmethod
    def from_proto(proto: protobuf.DaoStateStore):
        dao_state_hash_list = [DaoStateHash.from_proto(p) for p in proto.dao_state_hash]
        return DaoStateStore(proto.dao_state, dao_state_hash_list)

    def clear(self):
        self.dao_state_as_proto = None
        self.dao_state_hash_chain = None
