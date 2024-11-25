
from dataclasses import dataclass
from typing import TYPE_CHECKING

from bisq.common.crypto.encryption import Encryption

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric import dsa
    from bisq.common.protocol.network.network_envelope import NetworkEnvelope

@dataclass(frozen=True)
class DecryptedDataTuple:
    network_envelope: 'NetworkEnvelope'
    sig_public_key: 'dsa.DSAPublicKey'
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, DecryptedDataTuple):
            return False
        return (self.network_envelope == value.network_envelope and
                Encryption.is_pubkeys_equal(self.sig_public_key, value.sig_public_key))