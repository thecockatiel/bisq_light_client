from typing import TYPE_CHECKING, Sequence, Union

from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from electrum_ecc import ECPrivkey, ecdsa_der_sig_from_r_and_s

if TYPE_CHECKING:
    from electrum_min.keystore import BIP32_KeyStore


# TODO: implement as needed
class DeterministicKey:
    # A wrapper for KeyStoreWithMPK of electrum

    def __init__(
        self,
        pubkey: bytes,
        keystore: "BIP32_KeyStore",
        derivation_suffix: Sequence[int],
    ):
        self._keystore = keystore
        self._pubkey = pubkey
        self._pubkey_hash = None
        self._derivation_suffix = derivation_suffix
        assert (
            self._keystore.is_deterministic()
        ), "Keystore provided must be deterministic at DeterministicKey"

    def get_pub_key(self) -> bytes:
        """Gets the raw public key value. This appears in transaction scriptSigs. Note that this is not the same as the pubKeyHash address."""
        return self._pubkey

    def get_pub_key_hash(self) -> bytes:
        if self._pubkey_hash is None:
            self._pubkey_hash = get_sha256_ripemd160_hash(self._pubkey)
        return self._pubkey_hash

    def get_pub_key_as_hex(self) -> str:
        return self._pubkey.hex()

    def sign_message(self, message: Union[bytes, str], password: str = None):
        return self._keystore.sign_message(self._derivation_suffix, message, password)
    
    def ecdsa_sign(self, msg32: bytes, password: str = None, *, sigencode=ecdsa_der_sig_from_r_and_s):
        """Signs a message that is already hashed twice with SHA256."""
        if not isinstance(msg32, bytes) or len(msg32) != 32:
            raise IllegalArgumentException("msg32 must be 32 bytes long")
        privkey, compressed = self._keystore.get_private_key(self._derivation_suffix, password)
        key = ECPrivkey(privkey)
        return key.ecdsa_sign(msg32, sigencode=sigencode)
