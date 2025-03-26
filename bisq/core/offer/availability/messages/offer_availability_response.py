from dataclasses import dataclass, field
from typing import Optional

from bisq.common.capabilities import Capabilities
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.network.p2p.supported_capabilities_message import SupportedCapabilitiesMessage
from bisq.core.offer.availability.availability_result import AvailabilityResult
from bisq.core.offer.availability.messages.offer_message import OfferMessage
import pb_pb2 as protobuf
from utils.data import raise_required

@dataclass
class OfferAvailabilityResponse(OfferMessage, SupportedCapabilitiesMessage):
    offer_id: str = field(default_factory=raise_required)
    availability_result: AvailabilityResult = field(default_factory=raise_required)
    supported_capabilities: Optional[Capabilities] = field(default=None)
    arbitrator: NodeAddress = field(default_factory=raise_required)
    mediator: Optional[NodeAddress] = field(default=None)
    refund_agent: Optional[NodeAddress] = field(default=None)

    def to_proto_network_envelope(self):
        offer = protobuf.OfferAvailabilityResponse(
            offer_id=self.offer_id,
            availability_result=self.availability_result.to_proto_message()
        )
        
        if self.supported_capabilities:
            offer.supported_capabilities.extend(Capabilities.to_int_list(self.supported_capabilities))
        
        if self.uid:
            offer.uid = self.uid
        
        if self.mediator:
            offer.mediator.CopyFrom(self.mediator.to_proto_message())
        
        if self.refund_agent:
            offer.refund_agent.CopyFrom(self.refund_agent.to_proto_message())
        
        if self.arbitrator:
            offer.arbitrator.CopyFrom(self.arbitrator.to_proto_message())
        
        envelope = self.get_network_envelope_builder()
        envelope.offer_availability_response.CopyFrom(offer)
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.OfferAvailabilityResponse, message_version: int):
        return OfferAvailabilityResponse(
            message_version=message_version,
            offer_id=proto.offer_id,
            uid=proto.uid if proto.uid else None,
            availability_result=AvailabilityResult.from_proto(proto.availability_result),
            supported_capabilities=Capabilities.from_int_list(proto.supported_capabilities),
            arbitrator=NodeAddress.from_proto(proto.arbitrator) if proto.HasField('arbitrator') else None,
            mediator=NodeAddress.from_proto(proto.mediator) if proto.HasField('mediator') else None,
            refund_agent=NodeAddress.from_proto(proto.refund_agent) if proto.HasField('refund_agent') else None
        )