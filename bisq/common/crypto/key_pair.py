from dataclasses import dataclass
from typing import Union
from cryptography.hazmat.primitives.asymmetric.types import dsa, rsa
from cryptography.hazmat.primitives import serialization


@dataclass(frozen=True)
class KeyPair:
    private_key: Union[dsa.DSAPrivateKey, rsa.RSAPrivateKey]
    public_key: Union[dsa.DSAPublicKey, rsa.RSAPublicKey]

    def __eq__(self, other):
        return (
            isinstance(other, KeyPair)
            and self.private_key == other.private_key
            and self.public_key == other.public_key
        )

    def __hash__(self):
        return hash(
            (
                self.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                ),
                self.public_key.public_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ),
            )
        )
