# Singleton?

from typing import TYPE_CHECKING

from bisq.common.crypto.encryption import Encryption, rsa
from bisq.common.crypto.key_storage import KeyEntry
from bisq.common.crypto.pub_key_ring import PubKeyRing
from bisq.common.crypto.sig import Sig, dsa


if TYPE_CHECKING:
    from bisq.common.crypto.key_storage import KeyStorage


class KeyRing():
    def __init__(self, key_storage: 'KeyStorage'):
        if key_storage.all_key_files_exist():
            self.signature_key_pair = key_storage.load_key_pair(KeyEntry.MSG_SIGNATURE)
            self.encryption_key_pair = key_storage.load_key_pair(KeyEntry.MSG_ENCRYPTION)
        else:
            # First time we create key pairs
            self.signature_key_pair = Sig.generate_key_pair()
            self.encryption_key_pair = Encryption.generate_key_pair()
            key_storage.save_key_ring(self)
        self.pub_key_ring = PubKeyRing(signature_pub_key=self.signature_key_pair.public_key, encryption_pub_key=self.encryption_key_pair.public_key)
    
    def __str__(self) -> str:
        return f"KeyRing{{signatureKeyPair.hashCode()={hash(self.signature_key_pair)}, encryptionKeyPair.hashCode()={hash(self.encryption_key_pair)}, pubKeyRing.hashCode()={hash(self.pub_key_ring)}}}"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, KeyRing):
            return False
        return self.signature_key_pair == other.signature_key_pair and self.encryption_key_pair == other.encryption_key_pair
    
    def __hash__(self) -> int:
        return hash((self.signature_key_pair, self.encryption_key_pair))
