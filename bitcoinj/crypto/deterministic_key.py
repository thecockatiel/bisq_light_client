from typing import TYPE_CHECKING

from bisq.common.crypto.hash import get_sha256_ripemd160_hash

if TYPE_CHECKING:
    from electrum_min.keystore import KeyStoreWithMPK


# TODO: implement as needed
class DeterministicKey:
    # A wrapper for KeyStoreWithMPK of electrum

    def __init__(self, pubkey: bytes, keystore: "KeyStoreWithMPK"):
        self._keystore = keystore
        self._pubkey = pubkey
        self._pubkey_hash = None
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
