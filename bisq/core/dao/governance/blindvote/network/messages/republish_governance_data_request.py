# This message is sent only to full DAO nodes
from bisq.common.capabilities import Capabilities
from bisq.common.capability import Capability
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.direct_message import DirectMessage
from bisq.core.network.p2p.storage.payload.capability_requiring_payload import (
    CapabilityRequiringPayload,
)
import pb_pb2 as protobuf


class RepublishGovernanceDataRequest(
    NetworkEnvelope, DirectMessage, CapabilityRequiringPayload
):

    def to_proto_network_envelope(self):
        builder = self.get_network_envelope_builder()
        builder.republish_governance_data_request.CopyFrom(
            protobuf.RepublishGovernanceDataRequest()
        )

    @staticmethod
    def from_proto(
        proto: protobuf.RepublishGovernanceDataRequest, message_version: int
    ):
        return RepublishGovernanceDataRequest(message_version=message_version)

    def get_required_capabilities(self):
        return Capabilities(Capability.DAO_FULL_NODE)

    def __str__(self):
        return f"RepublishGovernanceDataRequest{{\n}} {super().__str__()}"
