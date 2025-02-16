from bisq.common.capabilities import Capabilities
from bisq.common.capability import Capability
from bisq.core.dao.monitoring.model.dao_state_hash import DaoStateHash
from bisq.core.dao.monitoring.network.messages.new_state_hash_message import (
    NewStateHashMessage,
)

import pb_pb2 as protobuf


class NewDaoStateHashMessage(NewStateHashMessage["DaoStateHash"]):

    def to_proto_network_envelope(self):
        builder = self.get_network_envelope_builder()
        builder.new_dao_state_hash_message.CopyFrom(
            protobuf.NewDaoStateHashMessage(
                state_hash=self.state_hash.to_proto_message()
            )
        )
        return builder

    @staticmethod
    def from_proto(proto: protobuf.NewDaoStateHashMessage, message_version: int):
        return NewDaoStateHashMessage(
            DaoStateHash.from_proto(proto.state_hash), message_version
        )

    def get_required_capabilities(self):
        return Capabilities([Capability.DAO_STATE])
