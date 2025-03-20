from typing import TYPE_CHECKING, Sequence, Union

from bisq.common.crypto.hash import get_sha256_ripemd160_hash

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

    def sign_message(self, message: Union[bytes, str], password: str = None) -> str:
        return self._keystore.sign_message(self._derivation_suffix, message, password)
