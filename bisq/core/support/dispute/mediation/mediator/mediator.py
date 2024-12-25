from typing import List, Dict, Optional

from bisq.common.crypto.pub_key_ring import PubKeyRing
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.support.dispute.agent.dispute_agent import DisputeAgent
import proto.pb_pb2 as protobuf

class Mediator(DisputeAgent):
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
            node_address,
            pub_key_ring,
            language_codes,
            registration_date,
            registration_pub_key,
            registration_signature,
            email_address,
            info,
            extra_data_map,
        )

    def to_proto_message(self):
        mediator = protobuf.Mediator(
            node_address=self.node_address.to_proto_message(),
            language_codes=self.language_codes,
            registration_date=self.registration_date,
            registration_pub_key=self.registration_pub_key,
            registration_signature=self.registration_signature,
            pub_key_ring=self.pub_key_ring.to_proto_message(),
        )
        if self.email_address:
            mediator.email_address = self.email_address
        if self.info:
            mediator.info = self.info
        if self.extra_data_map:
            mediator.extra_data.update(self.extra_data_map)

        return protobuf.StoragePayload(mediator=mediator)

    @staticmethod
    def from_proto(proto: protobuf.Mediator) -> "Mediator":
        return Mediator(
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

    def __str__(self) -> str:
        return f"Mediator{{{super().__str__()}}}"

    def __eq__(self, other) -> bool:
        return isinstance(other, Mediator) and super().__eq__(other)

    def __hash__(self):
        return super().__hash__()
    