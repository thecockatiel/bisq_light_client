from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from bisq.common.crypto.encryption import Encryption

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric import rsa
    from bisq.common.crypto.sig import DSA

@dataclass(frozen=True)
class KeyPair:
    private_key: Union["DSA.DsaKey", "rsa.RSAPrivateKey"]
    public_key: Union["DSA.DsaKey", "rsa.RSAPublicKey"]

    def __eq__(self, other):
        return (
            isinstance(other, KeyPair)
            and hash(self) == hash(other)
        )

    def __hash__(self):
        return hash(
            (
                Encryption.get_private_key_bytes(self.private_key),
                Encryption.get_public_key_bytes(self.public_key)
            )
        )
