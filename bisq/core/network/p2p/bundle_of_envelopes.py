 
from bisq.core.common.capabilities import Capabilities
from bisq.core.common.capability import Capability
from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.common.protocol.network.network_proto_resolver import NetworkProtoResolver
from bisq.core.common.protocol.protobuffer_exception import ProtobufferException
import bisq.core.common.version as Version 
from bisq.core.network.p2p.storage.broadcast_message import BroadcastMessage
from bisq.core.network.p2p.storage.payload.capability_requiring_payload import CapabilityRequiringPayload
import proto.pb_pb2 as protobuf

from typing import List, Optional

from dataclasses import dataclass, field

# @EqualsAndHashCode(callSuper = true)
@dataclass
class BundleOfEnvelopes(BroadcastMessage, CapabilityRequiringPayload):
    # Private final List<NetworkEnvelope> envelopes;
    envelopes: List[NetworkEnvelope] = field(default_factory=list)

    def __init__(self, envelopes: Optional[List[NetworkEnvelope]] = None):
        if envelopes is None:
            envelopes = []
        super().__init__(Version.get_p2p_message_version())
        self.envelopes = envelopes

    def add(self, network_envelope: NetworkEnvelope) -> None:
        self.envelopes.append(network_envelope)

    # PROTO BUFFER

    def to_proto_network_envelope(self) -> 'protobuf.NetworkEnvelope':
        return protobuf.NetworkEnvelope(bundle_of_envelopes=protobuf.BundleOfEnvelopes(envelopes=[env.to_proto_network_envelope() for env in self.envelopes]))

    @classmethod
    def from_proto(cls, proto: 'protobuf.BundleOfEnvelopes', resolver: NetworkProtoResolver, message_version: int) -> 'BundleOfEnvelopes':
        envelopes = []
        for envelope_proto in proto.envelopes:
            try:
                envelope = resolver.from_proto_network_envelope(envelope_proto)
                if envelope is not None:
                    envelopes.append(envelope)
            except ProtobufferException:
                continue
        return cls(envelopes=envelopes)

    # CapabilityRequiringPayload

    def get_required_capabilities(self) -> Capabilities:
        return Capabilities([Capability.BUNDLE_OF_ENVELOPES])