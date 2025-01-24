
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from bisq.common.capabilities import Capabilities
from bisq.common.crypto.pub_key_ring import PubKeyRing
from bisq.core.network.p2p.supported_capabilities_message import SupportedCapabilitiesMessage
from bisq.core.offer.availability.messages.offer_message import OfferMessage
import pb_pb2 as protobuf
from utils.data import raise_required

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_envelope import NetworkEnvelope

@dataclass
class OfferAvailabilityRequest(OfferMessage, SupportedCapabilitiesMessage):
    pub_key_ring: PubKeyRing = field(default_factory=raise_required)
    takers_trade_price: int = field(default_factory=raise_required)
    is_taker_api_user: bool = field(default_factory=raise_required)
    burning_man_selection_height: int = field(default_factory=raise_required)
    supported_capabilities: Optional[Capabilities] = field(default=None)

    def to_proto_network_envelope(self) -> 'NetworkEnvelope':
        offer = protobuf.OfferAvailabilityRequest(
            offer_id=self.offer_id,
            pub_key_ring=self.pub_key_ring.to_proto_message(),
            takers_trade_price=self.takers_trade_price,
            is_taker_api_user=self.is_taker_api_user,
            burning_man_selection_height=self.burning_man_selection_height
        )

        if self.supported_capabilities:
            offer.supported_capabilities.extend(Capabilities.to_int_list(self.supported_capabilities))

        if self.uid:
            offer.uid = self.uid

        envelope = self.get_network_envelope_builder()
        envelope.offer_availability_request.CopyFrom(offer)
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.OfferAvailabilityRequest, message_version: int) -> 'OfferAvailabilityRequest':
        return OfferAvailabilityRequest(
            message_version=message_version,
            offer_id=proto.offer_id,
            uid=None if not proto.uid else proto.uid,
            pub_key_ring=PubKeyRing.from_proto(proto.pub_key_ring),
            takers_trade_price=proto.takers_trade_price,
            is_taker_api_user=proto.is_taker_api_user,
            burning_man_selection_height=proto.burning_man_selection_height,
            supported_capabilities=Capabilities.from_int_list(proto.supported_capabilities),
        )