
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric import dsa
    from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope

@dataclass(frozen=True)
class DecryptedDataTuple:
    network_envelope: 'NetworkEnvelope'
    sig_public_key: 'dsa.DSAPublicKey'