from dataclasses import dataclass, field
from bisq.common.capabilities import Capabilities
from bisq.common.capability import Capability
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.direct_message import DirectMessage
from bisq.core.network.p2p.initial_data_request import InitialDataRequest
from bisq.core.network.p2p.storage.payload.capability_requiring_payload import (
    CapabilityRequiringPayload,
)
from utils.data import raise_required


@dataclass
class GetStateHashesRequest(
    NetworkEnvelope, DirectMessage, CapabilityRequiringPayload, InitialDataRequest
):
    height: int = field(default_factory=raise_required)
    nonce: int = field(default_factory=raise_required)

    def get_required_capabilities(self):
        return Capabilities([Capability.DAO_STATE])

    def __str__(self):
        return (
            f"GetStateHashesRequest{{\n"
            f"    height={self.height},\n"
            f"    nonce={self.nonce}\n"
            f"}} {super().__str__()}"
        )

    def __eq__(self, value):
        return (
            isinstance(value, GetStateHashesRequest)
            and value.height == self.height
            and value.nonce == self.nonce
        )

    def __hash__(self):
        return hash((self.height, self.nonce))
