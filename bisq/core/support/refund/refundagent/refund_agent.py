from typing import List, Optional, Dict

from bisq.common.capabilities import Capabilities
from bisq.common.capability import Capability
from bisq.common.crypto.pub_key_ring import PubKeyRing
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.network.p2p.storage.payload.capability_requiring_payload import (
    CapabilityRequiringPayload,
)
from bisq.core.support.dispute.agent.dispute_agent import DisputeAgent
from bisq.common.setup.log_setup import get_logger
import proto.pb_pb2 as protobuf

logger = get_logger(__name__)

class RefundAgent(DisputeAgent, CapabilityRequiringPayload):
    node_address: NodeAddress
    pub_key_ring: PubKeyRing
    language_codes: List[str]
    registration_date: int
    registration_pub_key: bytes
    registration_signature: str
    email_address: Optional[str] = None
    info: Optional[str] = None
    extra_data_map: Optional[Dict[str, str]] = None

    def __init__(
        self,
        node_address: NodeAddress,
        pub_key_ring: PubKeyRing,
        language_codes: List[str],
        registration_date: int,
        registration_pub_key: bytes,
        registration_signature: str,
        email_address: Optional[str] = None,
        info: Optional[str] = None,
        extra_data_map: Optional[Dict[str, str]] = None,
    ):
        super().__init__(
            node_address=node_address,
            pub_key_ring=pub_key_ring,
            language_codes=language_codes,
            registration_date=registration_date,
            registration_pub_key=registration_pub_key,
            registration_signature=registration_signature,
            email_address=email_address,
            info=info,
            extra_data_map=extra_data_map,
        )

    def to_proto_message(self):
        refund_agent = protobuf.RefundAgent(
            node_address=self.node_address.to_proto_message(),
            language_codes=self.language_codes,
            registration_date=self.registration_date,
            registration_pub_key=self.registration_pub_key,
            registration_signature=self.registration_signature,
            pub_key_ring=self.pub_key_ring.to_proto_message(),
        )

        if self.email_address:
            refund_agent.email_address = self.email_address
        if self.info:
            refund_agent.info = self.info
        if self.extra_data_map:
            refund_agent.extra_data.update(self.extra_data_map)

        return protobuf.StoragePayload(refund_agent=refund_agent)

    @staticmethod
    def from_proto(proto: "protobuf.RefundAgent") -> "RefundAgent":
        return RefundAgent(
            node_address=NodeAddress.from_proto(proto.node_address),
            pub_key_ring=PubKeyRing.from_proto(proto.pub_key_ring),
            language_codes=list(proto.language_codes),
            registration_date=proto.registration_date,
            registration_pub_key=proto.registration_pub_key,
            registration_signature=proto.registration_signature,
            email_address=ProtoUtil.string_or_none_from_proto(proto.email_address),
            info=ProtoUtil.string_or_none_from_proto(proto.info),
            extra_data_map=dict(proto.extra_data) if proto.extra_data else None,
        )

    def __str__(self):
        return f"RefundAgent() {super().__str__()}"

    def get_required_capabilities(self):
        return Capabilities([Capability.REFUND_AGENT])
