 
from bisq.common.capabilities import Capabilities
from bisq.common.capability import Capability
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver
from bisq.common.protocol.protobuffer_exception import ProtobufferException
from bisq.common.version import Version 
from bisq.core.network.p2p.extended_data_size_permission import ExtendedDataSizePermission
from bisq.core.network.p2p.storage.messages.broadcast_message import BroadcastMessage
from bisq.core.network.p2p.storage.payload.capability_requiring_payload import CapabilityRequiringPayload
import proto.pb_pb2 as protobuf

from typing import List, Optional

from dataclasses import dataclass, field

@dataclass
class BundleOfEnvelopes(BroadcastMessage, ExtendedDataSizePermission, CapabilityRequiringPayload):
    envelopes: list[NetworkEnvelope] = field(default_factory=list)

    def add(self, network_envelope: NetworkEnvelope) -> None:
        self.envelopes.append(network_envelope)

    # PROTO BUFFER

    def to_proto_network_envelope(self) -> 'protobuf.NetworkEnvelope':
        return protobuf.NetworkEnvelope(bundle_of_envelopes=protobuf.BundleOfEnvelopes(envelopes=[env.to_proto_network_envelope() for env in self.envelopes]))

    @staticmethod
    def from_proto(proto: 'protobuf.BundleOfEnvelopes', resolver: NetworkProtoResolver, message_version: int) -> 'BundleOfEnvelopes':
        envelopes = []
        for envelope_proto in proto.envelopes:
            try:
                envelope = resolver.from_proto(envelope_proto)
                if envelope is not None:
                    envelopes.append(envelope)
            except ProtobufferException:
                continue
        return BundleOfEnvelopes(envelopes=envelopes)

    def get_required_capabilities(self) -> Capabilities:
        return Capabilities([Capability.BUNDLE_OF_ENVELOPES])
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, BundleOfEnvelopes):
            return False
        return (self.message_version == other.message_version and
                self.envelopes == other.envelopes)

    def __hash__(self):
        return None