
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from bisq.core.common.capabilities import Capabilities
from bisq.core.common.crypto.pub_key_ring import PubKeyRing
from bisq.core.network.p2p.supported_capabilities_message import SupportedCapabilitiesMessage
from bisq.core.offer.availability.messages.offer_message import OfferMessage
import proto.pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope

@dataclass(frozen=True)
class OfferAvailabilityRequest(OfferMessage, SupportedCapabilitiesMessage):
    pub_key_ring: PubKeyRing
    takers_trade_price: int
    is_taker_api_user: bool
    burning_man_selection_height: int
    supported_capabilities: Optional[Capabilities] = None

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
        envelope.offer_availability_request = offer
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