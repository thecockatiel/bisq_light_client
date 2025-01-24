from typing import TYPE_CHECKING, Optional, Set, Dict
from bisq.common.capabilities import Capabilities
from bisq.common.capability import Capability
from bisq.core.network.p2p.storage.payload.capability_requiring_payload import CapabilityRequiringPayload
from bisq.core.network.p2p.storage.payload.proof_of_work_payload import ProofOfWorkPayload
from bisq.core.offer.offer_payload_base import OfferPayloadBase
from bisq.core.payment.bsq_swap_account import BsqSwapAccount
from bisq.core.payment.payload.payment_method import PaymentMethod
import pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.offer.offer_direction import OfferDirection
    from bisq.common.crypto.pub_key_ring import PubKeyRing
    from bisq.common.crypto.proof_of_work import ProofOfWork

class BsqSwapOfferPayload(OfferPayloadBase, ProofOfWorkPayload, CapabilityRequiringPayload):

    def __init__(self, id: str,
                 date: int,
                 owner_node_address: "NodeAddress",
                 pub_key_ring: "PubKeyRing",
                 direction: "OfferDirection",
                 price: int,
                 amount: int,
                 min_amount: int,
                 proof_of_work: "ProofOfWork",
                 extra_data_map: Optional[dict[str, str]] = None,
                 version_nr: str = None,
                 protocol_version: int = None):
        super().__init__(
            id=id,
            date=date,
            owner_node_address=owner_node_address,
            pub_key_ring=pub_key_ring,
            base_currency_code="BSQ",
            counter_currency_code="BTC",
            direction=direction,
            price=price,
            amount=amount,
            min_amount=min_amount,
            payment_method_id=PaymentMethod.BSQ_SWAP_ID,
            maker_payment_account_id=BsqSwapAccount.ID,
            extra_data_map=extra_data_map,
            version_nr=version_nr,
            protocol_version=protocol_version
        )
        self._proof_of_work = proof_of_work
        
    @staticmethod
    def from_other(original: "BsqSwapOfferPayload", offer_id: str, proof_of_work: "ProofOfWork"):
        return BsqSwapOfferPayload(
            id=offer_id,
            date=original.date,
            owner_node_address=original.owner_node_address,
            pub_key_ring=original.pub_key_ring,
            direction=original.direction,
            price=original.price,
            amount=original.amount,
            min_amount=original.min_amount,
            proof_of_work=proof_of_work,
            extra_data_map=original.extra_data_map,
            version_nr=original.version_nr,
            protocol_version=original.protocol_version
        )

    def to_proto_message(self) -> protobuf.StoragePayload:
        payload = protobuf.BsqSwapOfferPayload(
            id=self.id,
            date=self.date,
            owner_node_address=self.owner_node_address.to_proto_message(),
            pub_key_ring=self.pub_key_ring.to_proto_message(),
            direction=OfferDirection.to_proto_message(self.direction),
            price=self.price,
            amount=self.amount,
            min_amount=self.min_amount,
            proof_of_work=self._proof_of_work.to_proto_message(),
            version_nr=self.version_nr,
            protocol_version=self.protocol_version,
        )
        
        if self.extra_data_map:
            payload.extra_data.update(self.extra_data_map)
        return protobuf.StoragePayload(bsq_swap_offer_payload=payload)

    @staticmethod
    def from_proto(proto: protobuf.BsqSwapOfferPayload) -> "BsqSwapOfferPayload":
        extra_data_map = dict(proto.extra_data) if proto.extra_data else None
        return BsqSwapOfferPayload(
            id=proto.id,
            date=proto.date,
            owner_node_address=NodeAddress.from_proto(proto.owner_node_address),
            pub_key_ring=PubKeyRing.from_proto(proto.pub_key_ring),
            direction=OfferDirection.from_proto(proto.direction),
            price=proto.price,
            amount=proto.amount,
            min_amount=proto.min_amount,
            proof_of_work=ProofOfWork.from_proto(proto.proof_of_work),
            extra_data_map=extra_data_map,
            version_nr=proto.version_nr,
            protocol_version=proto.protocol_version
        )

    def get_required_capabilities(self):
        return Capabilities([Capability.BSQ_SWAP_OFFER])

    def __str__(self):
        return f"BsqSwapOfferPayload{{\n     proofOfWork={self._proof_of_work}\n}} " + super().__str__()

