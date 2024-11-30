# Supports signatures made from EC key (arbitrators) and signature created with DSA key.
from dataclasses import dataclass, field
from datetime import timedelta
from typing import ClassVar
import time
from bisq.common.capabilities import Capabilities
from bisq.common.capability import Capability
from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bisq.common.protocol.network.get_data_response_priority import GetDataResponsePriority
from bisq.core.account.sign.signed_witness_verification_method import SignedWitnessVerificationMethod
from bisq.core.network.p2p.storage.payload.capability_requiring_payload import (
    CapabilityRequiringPayload,
)
from bisq.core.network.p2p.storage.payload.data_tolerant_payload import (
    DateTolerantPayload,
)
from bisq.core.network.p2p.storage.payload.persistable_network_payload import (
    PersistableNetworkPayload,
)
from bisq.core.network.p2p.storage.payload.process_once_persistable_network_payload import (
    ProcessOncePersistableNetworkPayload,
)
from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray
import proto.pb_pb2 as protobuf
from utils.clock import Clock


@dataclass
class SignedWitness(
    ProcessOncePersistableNetworkPayload,
    DateTolerantPayload,
    PersistableNetworkPayload,
    CapabilityRequiringPayload,
):
    TOLERANCE: ClassVar[int] = int(
        timedelta(days=1).total_seconds() * 1000
    )  # 1 day in milliseconds

    verification_method: SignedWitnessVerificationMethod
    account_age_witness_hash: bytes
    signature: bytes
    signer_pub_key: bytes
    witness_owner_pub_key: bytes
    date: int
    trade_amount: int

    hash: bytes = field(init=False, repr=False, hash=False, compare=False)

    def __post_init__(self):
        # The hash is only using the data which does not change in repeated trades between identical users (no date or amount).
        # We only want to store the first and oldest one and will ignore others. That will also help to protect privacy
        # so that the total number of trades is not revealed. We use putIfAbsent when we store the data so first
        # object will win. We consider one signed trade with one peer enough and do not consider repeated trades with
        # same peer to add more security as if that one would be colluding it would be not detected anyway. The total
        # number of signed trades with different peers is still available and can be considered more valuable data for
        # security.
        data = self.account_age_witness_hash + self.signature + self.signer_pub_key
        self.hash = get_sha256_ripemd160_hash(data)

    def to_proto_message(self):
        builder = protobuf.SignedWitness(
            verification_method=SignedWitnessVerificationMethod.to_proto_message(self.verification_method),
            account_age_witness_hash=self.account_age_witness_hash,
            signature=self.signature,
            signer_pub_key=self.signer_pub_key,
            witness_owner_pub_key=self.witness_owner_pub_key,
            date=self.date,
            trade_amount=self.trade_amount,
        )
        return protobuf.PersistableNetworkPayload(signed_witness=builder)
    
    def to_proto_signed_witness(self):
        return self.to_proto_message().signed_witness

    @staticmethod
    def from_proto(proto: protobuf.SignedWitness):
        return SignedWitness(
            verification_method=SignedWitnessVerificationMethod.from_proto(
                proto.verification_method
            ),
            account_age_witness_hash=proto.account_age_witness_hash,
            signature=proto.signature,
            signer_pub_key=proto.signer_pub_key,
            witness_owner_pub_key=proto.witness_owner_pub_key,
            date=proto.date,
            trade_amount=proto.trade_amount,
        )
    
    def get_data_response_priority(self) -> GetDataResponsePriority:
        return GetDataResponsePriority.MID

    def is_date_in_tolerance(self, clock: Clock):
        # We don't allow older or newer than 1 day.
        # Preventing forward dating is also important to protect against a sophisticated attack
        return abs(clock.millis() - self.date) <= self.TOLERANCE

    def verify_hash_size(self):
        return len(self.hash) == 20

    # Pre 1.0.1 version don't know the new message type and throw an error which leads to disconnecting the peer.
    def get_required_capabilities(self):
        return Capabilities([Capability.SIGNED_ACCOUNT_AGE_WITNESS])

    def get_hash(self):
        return self.hash

    @property
    def is_signed_by_arbitrator(self):
        return self.verification_method == SignedWitnessVerificationMethod.ARBITRATOR
    
    def get_hash_as_byte_array(self):
        return StorageByteArray(self.hash)

    def __str__(self):
        return (
            f"SignedWitness{{\n"
            f"     verificationMethod={self.verification_method},\n"
            f"     witnessHash={self.account_age_witness_hash.hex()},\n"
            f"     signature={self.signature.hex()},\n"
            f"     signerPubKey={self.signer_pub_key.hex()},\n"
            f"     witnessOwnerPubKey={self.witness_owner_pub_key.hex()},\n"
            f"     date={time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(self.date / 1000))},\n"
            f"     tradeAmount={self.trade_amount},\n"
            f"     hash={self.hash.hex()}\n"
            f"}}"
        )
