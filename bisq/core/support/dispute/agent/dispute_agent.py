from abc import ABC
from datetime import timedelta
from typing import List, Dict, Optional, Any

from bisq.common.crypto.pub_key_ring import PubKeyRing
from bisq.common.protocol.network.get_data_response_priority import GetDataResponsePriority
from bisq.common.util.extra_data_map_validator import ExtraDataMapValidator
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.network.p2p.storage.payload.expirable_payload import ExpirablePayload
from bisq.core.network.p2p.storage.payload.protected_storage_payload import ProtectedStoragePayload

class DisputeAgent(ProtectedStoragePayload, ExpirablePayload, ABC):
    TTL = int(timedelta(days=10).total_seconds() * 1000)  # Convert to milliseconds

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
        extra_data_map: Optional[Dict[str, str]] = None
    ):
        super().__init__()
        self.node_address = node_address
        self.pub_key_ring = pub_key_ring
        self.language_codes = language_codes
        self.registration_date = registration_date
        self.registration_pub_key = registration_pub_key
        self.registration_signature = registration_signature
        self.email_address = email_address
        self.info = info
        # Should be only used in emergency case if we need to add data but do not want to break backward compatibility
        # at the P2P network storage checks. The hash of the object will be used to verify if the data is valid. Any new
        # field in a class would break that hash and therefore break the storage mechanism.
        self.extra_data_map = ExtraDataMapValidator.get_validated_extra_data_map(extra_data_map)
 
    def get_data_response_priority(self) -> str:
        return GetDataResponsePriority.HIGH

    def get_ttl(self) -> int:
        return self.TTL

    def get_owner_pub_key(self):
        return self.pub_key_ring.signature_pub_key
    
    def get_extra_data_map(self):
        return self.extra_data_map

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, DisputeAgent):
            return False
        return (
            self.node_address == other.node_address and
            self.pub_key_ring == other.pub_key_ring and
            self.language_codes == other.language_codes and
            self.registration_date == other.registration_date and
            self.registration_pub_key == other.registration_pub_key and
            self.registration_signature == other.registration_signature and
            self.email_address == other.email_address and
            self.info == other.info and
            self.extra_data_map == other.extra_data_map
        )
        
    def __hash__(self) -> int:
        return hash((
            self.node_address,
            self.pub_key_ring,
            self.registration_date,
            self.registration_pub_key,
            self.registration_signature,
            self.email_address,
            self.info,
        ))

    def __str__(self) -> str:
        return (
            "DisputeAgent{\n"
            f"    node_address={self.node_address},\n"
            f"    pub_key_ring={self.pub_key_ring},\n"
            f"    language_codes={self.language_codes},\n"
            f"    registration_date={self.registration_date},\n"
            f"    registration_pub_key={self.registration_pub_key.hex()},\n"
            f"    registration_signature='{self.registration_signature}',\n"
            f"    email_address='{self.email_address}',\n"
            f"    info='{self.info}',\n"
            f"    extra_data_map={self.extra_data_map}\n"
            "}"
        )